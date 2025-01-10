import json
import time
from collections import Counter, defaultdict
from textwrap import dedent
from typing import Iterable

import dagster as dg
import dagster_duckdb as dg_duckdb
import pandas as pd
from dagster_openai import OpenAIResource
from openai import OpenAI

import project_llm_fine_fune.constants as constants
import project_llm_fine_fune.utils as utils

goodreads = dg.AssetSpec(
    "goodreads_source_dataset",
    description="Goodreads Data. https://mengtingwan.github.io/data/goodreads#datasets",
    group_name="raw_data",
)


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


@dg.asset(
    kinds={"duckdb"},
    description="Goodreads shelf feature engineering",
    group_name="feature_engineering",
)
def book_category(
    duckdb_resource: dg_duckdb.DuckDBResource,
    graphic_novels,
):
    sql_categories = ", ".join([f"'{s}'" for s in constants.CATEGORIES])
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
    query = f"""
        create table if not exists enriched_graphic_novels as ( 
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
        );
    """
    with duckdb_resource.get_connection() as conn:
        conn.execute(query)
        select_query = """
            select * from enriched_graphic_novels;
        """
        return conn.execute(select_query).fetch_df()


def create_prompt_record(data: dict, categories: list):
    return {
        "messages": [
            {
                "role": "system",
                "content": f"Given an author, title and book description, what category is it? Here are the possible categories {", ".join(categories)}",
            },
            {
                "role": "user",
                "content": f"What category is {data['title']} by {data["author"]}? Description: {data["description"]}",
            },
            {
                "role": "assistant",
                "content": data["category"],
                "weight": 1,
            },
        ]
    }


@dg.asset(
    kinds={"python"},
    group_name="preparation",
    description="Generate training file",
)
def training_file(
    enriched_graphic_novels,
) -> str:
    graphic_novels = enriched_graphic_novels.sample(n=constants.TRAINING_FILE_NUM)
    prompt_data = []
    for record in [row for _, row in graphic_novels.iterrows()]:
        prompt_data.append(create_prompt_record(record, constants.CATEGORIES))

    file_name = "goodreads-training.jsonl"
    utils.write_openai_file(file_name, prompt_data)
    return file_name


@dg.asset(
    kinds={"python"},
    group_name="preparation",
    description="Generate validation file",
)
def validation_file(
    enriched_graphic_novels,
) -> str:
    graphic_novels = enriched_graphic_novels.sample(n=constants.VALIDATION_FILE_NUM)
    prompt_data = []
    for record in [row for _, row in graphic_novels.iterrows()]:
        prompt_data.append(create_prompt_record(record, constants.CATEGORIES))

    file_name = "goodreads-validation.jsonl"
    utils.write_openai_file(file_name, prompt_data)
    return file_name


def openai_file_validation(file_name: str) -> Iterable:
    format_errors = defaultdict(int)
    for ex in utils.read_openai_file(file_name):
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
                k not in ("role", "content", "name", "function_call", "weight")
                for k in message
            ):
                format_errors["message_unrecognized_key"] += 1

            if message.get("role", None) not in (
                "system",
                "user",
                "assistant",
                "function",
            ):
                format_errors["unrecognized_role"] += 1

            content = message.get("content", None)
            function_call = message.get("function_call", None)

            if (not content and not function_call) or not isinstance(content, str):
                format_errors["missing_content"] += 1

        if not any(message.get("role", None) == "assistant" for message in messages):
            format_errors["example_missing_assistant_message"] += 1

    if format_errors:
        yield dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description="Training data set has errors",
            metadata=format_errors,
        )
    else:
        yield dg.AssetCheckResult(
            passed=True,
            description="Training data set is ready to upload",
        )


@dg.asset_check(
    asset=training_file,
    description="Validation for fine-tuning data file from OpenAI cookbook",
    metadata={
        "source": "https://cookbook.openai.com/examples/chat_finetuning_data_prep#format-validation"
    },
)
def training_file_format_check():
    openai_file_validation("goodreads-training.jsonl")


@dg.asset_check(
    asset=validation_file,
    description="Validation for fine-tuning data file from OpenAI cookbook",
    metadata={
        "source": "https://cookbook.openai.com/examples/chat_finetuning_data_prep#format-validation"
    },
)
def validation_file_format_check():
    openai_file_validation("goodreads-validation.jsonl")


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
            model=constants.MODEL_NAME,
            suffix="goodreads",
        )

    create_job_id = create_job_resp.to_dict()["id"]
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
    return fine_tuned_model_name


def model_question(
    client: OpenAI,
    model: str,
    data: dict,
    categories: list,
) -> str:
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
    return json.loads(content)["category"]


@dg.asset_check(
    asset=fine_tuned_model,
    description="Compare fine-tuned model against base model accuracy",
)
def fine_tuned_model_accuracy(
    context: dg.AssetCheckExecutionContext,
    duckdb_resource: dg_duckdb.DuckDBResource,
    openai: OpenAIResource,
    fine_tuned_model,
) -> Iterable[dg.AssetCheckResult]:
    query = f"""
        select * from enriched_graphic_novels
    """
    with duckdb_resource.get_connection() as conn:
        validation = (
            conn.execute(query).fetch_df().sample(n=constants.VALIDATION_SAMPLE_SIZE)
        )

    models = Counter()
    base_model = constants.MODEL_NAME
    with openai.get_client(context) as client:
        for data in [row for _, row in validation.iterrows()]:
            for model in [fine_tuned_model, base_model]:
                model_answer = model_question(
                    client,
                    model,
                    data,
                    categories=constants.CATEGORIES,
                )
                if model_answer == data["category"]:
                    models[model] += 1

    model_accuracy={
        fine_tuned_model: models[fine_tuned_model] / constants.VALIDATION_SAMPLE_SIZE,
        base_model: models[base_model] / constants.VALIDATION_SAMPLE_SIZE,
    }

    if model_accuracy[fine_tuned_model] < model_accuracy[base_model]:
        yield dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.WARN,
            description=f"{fine_tuned_model} has lower accuracy than {base_model}",
            metadata=model_accuracy,
        )
    else:
        yield dg.AssetCheckResult(
            passed=True,
            metadata=model_accuracy,
        )
