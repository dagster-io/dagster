import dagster as dg
import pandas as pd
from collections import defaultdict
import time
from dagster_openai import OpenAIResource
import dagster_duckdb as dg_duckdb
from . import utils
import json
from textwrap import dedent
from collections import Counter
from openai import OpenAI
from typing import Iterable
import project_llm_fine_fune.constants as constants


goodreads = dg.AssetSpec(
    "Goodreads",
    description="Goodreads Data. https://mengtingwan.github.io/data/goodreads#datasets",
    group_name="raw_data",
)


@dg.asset(
    kinds={"duckdb"},
    description="Goodreads graphic novel data",
    group_name="processing",
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
    group_name="processing",
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
    group_name="processing",
)
def manga_shelf(duckdb_resource: dg_duckdb.DuckDBResource, graphic_novels):
    query = f"""
        create table if not exists manga_shelf as (
            select
            book_id,
            (case when sum(manga) > 1 then 'true' else 'false' end) is_manga
            from (
            select
                book_id,
                (case when unnest(popular_shelves).name like '%manga%' then 1 else 0 end) as manga
            from graphic_novels
            )
            group by 1
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
    manga_shelf,
) -> pd.DataFrame:
    query = f"""
        create table if not exists enriched_graphic_novels as (
            select
            book.title as title,
            authors.name as author,
            book.description as description,
            manga_shelf.is_manga
            from graphic_novels as book
            left join authors
            on book.authors[1].author_id = authors.author_id
            left join manga_shelf
            on book.book_id = manga_shelf.book_id
            where nullif(book.description, '') is not null
        )
    """
    with duckdb_resource.get_connection() as conn:
        conn.execute(query)
        select_query = """
            select * from enriched_graphic_novels
        """
        return conn.execute(select_query).fetch_df()


def create_prompt_record(data: dict):
    return {
        "messages": [
            {
                "role": "system",
                "content": "Given an author, title and book description, is title manga?",
            },
            {
                "role": "user",
                "content": f"{data['title']} by {data['author']} described as: {data['description']}. Is this a manga?",
            },
            {
                "role": "assistant",
                "content": data["is_manga"],
                "weight": 1,
            },
        ]
    }


@dg.asset(
    group_name="preparation",
    description="Generate training file",
)
def training_file(
    enriched_graphic_novels,
) -> str:
    graphic_novels = enriched_graphic_novels.sample(n=constants.TRAINING_FILE_NUM)
    prompt_data = []
    for record in [row for _, row in graphic_novels.iterrows()]:
        prompt_data.append(create_prompt_record(record))

    file_name = "goodreads-training.jsonl"
    utils.write_openai_file(file_name, prompt_data)
    return file_name


@dg.asset(
    group_name="preparation",
    description="Generate validation file",
)
def validation_file(
    enriched_graphic_novels,
) -> str:
    graphic_novels = enriched_graphic_novels.sample(n=constants.VALIDATION_FILE_NUM)
    prompt_data = []
    for record in [row for _, row in graphic_novels.iterrows()]:
        prompt_data.append(create_prompt_record(record))

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
    kinds={"OpenAI"},
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
    kinds={"OpenAI"},
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
    kinds={"OpenAI"},
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


def model_question(client: OpenAI, model: str, prompt: str, question: str) -> bool:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": dedent(prompt),
            },
            {"role": "user", "content": dedent(question)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "is_manga",
                "schema": {
                    "type": "object",
                    "properties": {"is_manga": {"type": "boolean"}},
                    "required": ["is_manga"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    )
    content = completion.choices[0].message.content
    return json.loads(content)["is_manga"]


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
    models = Counter()
    prompt = """
        You will be provided with the title, author and description of a book.
        Determine if the title is or is not manga.
    """
    query = f"""
        select * from enriched_graphic_novels
    """
    with duckdb_resource.get_connection() as conn:
        asset_check_validation = (
            conn.execute(query).fetch_df().sample(constants.VALIDATION_SAMPLE_SIZE)
        )

    with openai.get_client(context) as client:
        for data in [row for _, row in asset_check_validation.iterrows()]:
            for model in [fine_tuned_model, constants.MODEL_NAME]:
                question = f"""
                    Is {data["title"]} by {data["author"]} manga?
                    Here is a description of the title: {data["description"]}
                """
                model_answer = model_question(client, model, prompt, question)

                if model_answer == bool(data["is_manga"]):
                    models[model] += 1

    fine_tuned_model_accuracy = models[fine_tuned_model] / constants.VALIDATION_SAMPLE_SIZE
    base_model_accuracy = models[constants.MODEL_NAME] / constants.VALIDATION_SAMPLE_SIZE

    if fine_tuned_model_accuracy > base_model_accuracy:
        yield dg.AssetCheckResult(
            passed=True,
            description=f"{fine_tuned_model}: {fine_tuned_model_accuracy} greater than {base_model_accuracy} base",
        )
    else:
        yield dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.WARN,
            description=f"{fine_tuned_model}: {fine_tuned_model_accuracy} lower than {base_model_accuracy} base",
        )
