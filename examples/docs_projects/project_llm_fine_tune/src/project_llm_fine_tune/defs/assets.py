import json
import time
from collections import Counter, defaultdict
from collections.abc import Generator, Iterable
from textwrap import dedent

import dagster as dg
import dagster_duckdb as dg_duckdb
import pandas as pd
from dagster_openai import OpenAIResource
from openai import OpenAI

MODEL_NAME = "gpt-4o-mini-2024-07-18"
TRAINING_FILE_NUM = 50
VALIDATION_FILE_NUM = 50
VALIDATION_SAMPLE_SIZE = 100
CATEGORIES = [
    "fantasy",
    "horror",
    "humor",
    "adventure",
    "action",
    "romance",
    "ya",
    "superheroes",
    "comedy",
    "mystery",
    "supernatural",
    "drama",
]


def write_openai_file(file_name: str, data: list):
    """Writes the contents of list to file.

    Args:
        file_name (str): name of the output file
        data (list): data to write to file

    """
    with open(file_name, "w") as output_file:
        for i, row in enumerate(data):
            output_file.write(json.dumps(row))
            if i < len(data) - 1:
                output_file.write("\n")


def read_openai_file(file_name: str) -> Generator:
    """Reads the contents of a file.

    Args:
        file_name (str): name of the input file

    Returns:
        Generator: records of the jsonl file as dicts

    """
    with open(file_name) as training_file:
        for line in training_file:
            if line.strip():
                yield json.loads(line)


goodreads = dg.AssetSpec(
    "goodreads_source_dataset",
    description="Goodreads Data. https://mengtingwan.github.io/data/goodreads#datasets",
    group_name="raw_data",
)


# start_graphic_novel
@dg.asset(
    kinds={"duckdb"},
    description="Goodreads graphic novel data",
    group_name="ingestion",
    deps=[goodreads],
)
def graphic_novels(duckdb_resource: dg_duckdb.DuckDBResource):
    url = "https://datarepo.eng.ucsd.edu/mcauley_group/gdrive/goodreads/byGenre/goodreads_books_comics_graphic.json.gz"
    query = f"""
        create table if not exists graphic_novels as (
            select *
            from read_json(
                '{url}',
                ignore_errors = true
            )
        );
    """
    with duckdb_resource.get_connection() as conn:
        conn.execute(query)


# end_graphic_novel


@dg.asset(
    kinds={"duckdb"},
    description="Goodreads author data",
    group_name="ingestion",
    deps=[goodreads],
)
def authors(duckdb_resource: dg_duckdb.DuckDBResource):
    url = "https://datarepo.eng.ucsd.edu/mcauley_group/gdrive/goodreads/goodreads_book_authors.json.gz"
    query = f"""
        create table if not exists authors as (
            select *
            from read_json(
                '{url}',
                ignore_errors = true
            )
        );
    """
    with duckdb_resource.get_connection() as conn:
        conn.execute(query)


# start_book_category
@dg.asset(
    kinds={"duckdb"},
    description="Goodreads shelf feature engineering",
    group_name="feature_engineering",
)
def book_category(
    duckdb_resource: dg_duckdb.DuckDBResource,
    graphic_novels,
):
    sql_categories = ", ".join([f"'{s}'" for s in CATEGORIES])
    query = f"""
        create table if not exists book_category as (
            select
            book_id,
            category
            from (
                select
                book_id,
                category,
                category_count,
                row_number() over (partition by book_id order by category_count desc) as category_rank
                from (
                    select
                    book_id,
                    shelf.name as category,
                    cast(shelf.count as integer) as category_count
                    from (
                        select
                            book_id,
                            unnest(popular_shelves) as shelf
                        from graphic_novels
                    )
                    where category in ({sql_categories})
                    and category_count > 3
                )
            )
            where category_rank = 1
        );
    """
    with duckdb_resource.get_connection() as conn:
        conn.execute(query)


# end_book_category


# start_enriched_graphic_novels
@dg.asset(
    kinds={"duckdb"},
    description="Combined book, author and shelf data",
    group_name="processing",
)
def enriched_graphic_novels(
    duckdb_resource: dg_duckdb.DuckDBResource,
    graphic_novels,
    authors,
    book_category,
) -> pd.DataFrame:
    query = """
        select
            book.title as title,
            authors.name as author,
            book.description as description,
            book_category.category
        from graphic_novels as book
        left join authors
            on book.authors[1].author_id = authors.author_id
        left join book_category
            on book.book_id = book_category.book_id
        where nullif(book.description, '') is not null
        and category is not null
    """
    with duckdb_resource.get_connection() as conn:
        return conn.execute(query).fetch_df()


# end_enriched_graphic_novels


# start_prompt_record
def create_prompt_record(data: dict, categories: list):
    return {
        "messages": [
            {
                "role": "system",
                "content": f"Given an author, title and book description, what category is it? Here are the possible categories {', '.join(categories)}",
            },
            {
                "role": "user",
                "content": f"What category is {data['title']} by {data['author']}? Description: {data['description']}",
            },
            {
                "role": "assistant",
                "content": data["category"],
                "weight": 1,
            },
        ]
    }


# end_prompt_record


# start_training_file
@dg.asset(
    kinds={"python"},
    group_name="preparation",
    description="Generate training file",
)
def training_file(
    enriched_graphic_novels,
) -> str:
    graphic_novels = enriched_graphic_novels.sample(n=TRAINING_FILE_NUM)
    prompt_data = []
    for record in [row for _, row in graphic_novels.iterrows()]:
        prompt_data.append(create_prompt_record(record, CATEGORIES))

    file_name = "goodreads-training.jsonl"
    write_openai_file(file_name, prompt_data)
    return file_name


# end_training_file


@dg.asset(
    kinds={"python"},
    group_name="preparation",
    description="Generate validation file",
)
def validation_file(
    enriched_graphic_novels,
) -> str:
    graphic_novels = enriched_graphic_novels.sample(n=VALIDATION_FILE_NUM)
    prompt_data = []
    for record in [row for _, row in graphic_novels.iterrows()]:
        prompt_data.append(create_prompt_record(record, CATEGORIES))

    file_name = "goodreads-validation.jsonl"
    write_openai_file(file_name, prompt_data)
    return file_name


# start_file_validation
def openai_file_validation(data: Iterable) -> dg.AssetCheckResult:
    format_errors = defaultdict(int)
    for ex in data:
        if not isinstance(ex, dict):
            format_errors["data_type"] += 1
            continue

        messages = ex.get("messages", None)
        if not messages:
            format_errors["missing_messages_list"] += 1
            continue

        for message in messages:
            if "role" not in message or "content" not in message:
                format_errors["message_missing_key"] += 1

            if any(
                k not in ("role", "content", "name", "function_call", "weight") for k in message
            ):
                format_errors["message_unrecognized_key"] += 1

            if message.get("role", None) not in ("system", "user", "assistant", "function"):
                format_errors["unrecognized_role"] += 1

            content = message.get("content", None)
            function_call = message.get("function_call", None)

            if (not content and not function_call) or not isinstance(content, str):
                format_errors["missing_content"] += 1

        if not any(message.get("role", None) == "assistant" for message in messages):
            format_errors["example_missing_assistant_message"] += 1

    if format_errors:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description="Training data set has errors",
            metadata=format_errors,
        )
    else:
        return dg.AssetCheckResult(
            passed=True,
            description="Training data set is ready to upload",
        )


# end_file_validation


# start_asset_check
@dg.asset_check(
    asset=training_file,
    description="Validation for fine-tuning data file from OpenAI cookbook",
    metadata={
        "source": "https://cookbook.openai.com/examples/chat_finetuning_data_prep#format-validation"
    },
)
def training_file_format_check() -> dg.AssetCheckResult:
    data = read_openai_file("goodreads-training.jsonl")
    return openai_file_validation(data)


# end_asset_check


@dg.asset_check(
    asset=validation_file,
    description="Validation for fine-tuning data file from OpenAI cookbook",
    metadata={
        "source": "https://cookbook.openai.com/examples/chat_finetuning_data_prep#format-validation"
    },
)
def validation_file_format_check() -> dg.AssetCheckResult:
    data = read_openai_file("goodreads-validation.jsonl")
    return openai_file_validation(data)


# start_upload_file
@dg.asset(
    kinds={"openai"},
    description="Upload training set",
    group_name="fine_tuning",
)
def upload_training_file(
    context: dg.AssetExecutionContext,
    openai: OpenAIResource,
    training_file,
) -> str:
    with openai.get_client(context) as client:
        with open(training_file, "rb") as file_fd:
            response = client.files.create(file=file_fd, purpose="fine-tune")
    return response.id


# end_upload_file


@dg.asset(
    kinds={"openai"},
    description="Upload validation file to OpenAI",
    group_name="fine_tuning",
)
def upload_validation_file(
    context: dg.AssetExecutionContext,
    openai: OpenAIResource,
    validation_file,
) -> str:
    with openai.get_client(context) as client:
        with open(validation_file, "rb") as file_fd:
            response = client.files.create(file=file_fd, purpose="fine-tune")
    return response.id


# start_fine_tuned_model
@dg.asset(
    kinds={"openai"},
    description="Exeute model fine-tuning job",
    group_name="fine_tuning",
)
def fine_tuned_model(
    context: dg.AssetExecutionContext,
    openai: OpenAIResource,
    upload_training_file,
    upload_validation_file,
) -> str:
    with openai.get_client(context) as client:
        create_job_resp = client.fine_tuning.jobs.create(
            training_file=upload_training_file,
            validation_file=upload_validation_file,
            model=MODEL_NAME,
            suffix="goodreads",
        )

    create_job_id = str(create_job_resp.to_dict()["id"])
    context.log.info(f"Fine tuning job: {create_job_id}")

    while True:
        status_job_resp = client.fine_tuning.jobs.retrieve(create_job_id)
        status = status_job_resp.to_dict()["status"]
        context.log.info(f"Job {create_job_id}: {status}")
        if status in ["succeeded", "cancelled", "failed"]:
            break
        time.sleep(30)

    fine_tuned_model_name = status_job_resp.to_dict()["fine_tuned_model"]
    context.add_output_metadata({"model_name": fine_tuned_model_name})
    return str(fine_tuned_model_name)


# end_fine_tuned_model


def model_question(
    client: OpenAI,
    model: str,
    data: dict,
    categories: list,
):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": dedent(
                    """
                    You will be provided with the title, author and description of a book.
                    Determine the category.
                """,
                ),
            },
            {
                "role": "user",
                "content": dedent(
                    f"""
                    What category is {data["title"]} by {data["author"]}?
                    Description: {data["description"]}
                """,
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "category",
                "schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": categories,
                        }
                    },
                    "required": ["category"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    )
    content = completion.choices[0].message.content
    assert content is not None
    return json.loads(content)["category"]


# start_model_validation
@dg.asset_check(
    asset=fine_tuned_model,
    additional_ins={"data": dg.AssetIn("enriched_graphic_novels")},
    description="Compare fine-tuned model against base model accuracy",
)
def fine_tuned_model_accuracy(
    context: dg.AssetCheckExecutionContext,
    openai: OpenAIResource,
    fine_tuned_model,
    data,
) -> dg.AssetCheckResult:
    validation = data.sample(n=VALIDATION_SAMPLE_SIZE)

    models = Counter()
    base_model = MODEL_NAME
    with openai.get_client(context) as client:
        for data in [row for _, row in validation.iterrows()]:
            for model in [fine_tuned_model, base_model]:
                model_answer = model_question(
                    client,
                    model,
                    data,
                    categories=CATEGORIES,
                )
                if model_answer == data["category"]:
                    models[model] += 1

    model_accuracy = {
        fine_tuned_model: models[fine_tuned_model] / VALIDATION_SAMPLE_SIZE,
        base_model: models[base_model] / VALIDATION_SAMPLE_SIZE,
    }

    if model_accuracy[fine_tuned_model] < model_accuracy[base_model]:
        return dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.WARN,
            description=f"{fine_tuned_model} has lower accuracy than {base_model}",
            metadata=model_accuracy,
        )
    else:
        return dg.AssetCheckResult(
            passed=True,
            metadata=model_accuracy,
        )


# end_model_validation
