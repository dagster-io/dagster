from typing import Any, Dict, List

from dagster import (
    AllPartitionMapping,
    AssetExecutionContext,
    AssetIn,
    Config,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
)
from dagster_openai import OpenAIResource
from langchain.chains.qa_with_sources import stuff_prompt
from langchain.docstore.document import Document
from langchain.schema.output_parser import StrOutputParser
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .constants import SUMMARY_TEMPLATE
from .utils import get_github_docs

docs_partitions_def = StaticPartitionsDefinition(
    [
        "about",
        "community",
        "concepts",
        "dagster-plus",
        "deployment",
        "getting-started",
        "guides",
        "integrations",
        "tutorial",
    ]
)


@asset(compute_kind="GitHub", partitions_def=docs_partitions_def)
def source_docs(context: AssetExecutionContext):
    return list(get_github_docs("dagster-io", "dagster", context.partition_key))


@asset(compute_kind="OpenAI", partitions_def=docs_partitions_def)
def search_index(context: AssetExecutionContext, openai: OpenAIResource, source_docs: list[Any]):
    source_chunks = []
    splitter = CharacterTextSplitter(separator=" ", chunk_size=1024, chunk_overlap=0)
    for source in source_docs:
        context.log.info(source)
        for chunk in splitter.split_text(source.page_content):
            source_chunks.append(Document(page_content=chunk, metadata=source.metadata))

    with openai.get_client(context) as client:
        search_index = FAISS.from_documents(
            source_chunks, OpenAIEmbeddings(client=client.embeddings)
        )

    return search_index.serialize_to_bytes()


class OpenAIConfig(Config):
    model: str
    question: str


@asset(
    compute_kind="OpenAI",
    ins={
        "search_index": AssetIn(partition_mapping=AllPartitionMapping()),
    },
)
def completion(
    context: AssetExecutionContext,
    openai: OpenAIResource,
    config: OpenAIConfig,
    search_index: dict[str, Any],
):
    merged_index: Any = None
    # allow_dangerous_deserialization set to True since since we created the search index ourselves
    # in the search_index asset
    for index in search_index.values():
        curr = FAISS.deserialize_from_bytes(
            index, OpenAIEmbeddings(), allow_dangerous_deserialization=True
        )
        if not merged_index:
            merged_index = curr
        else:
            merged_index.merge_from(
                FAISS.deserialize_from_bytes(
                    index, OpenAIEmbeddings(), allow_dangerous_deserialization=True
                )
            )
    with openai.get_client(context) as client:
        prompt = stuff_prompt.PROMPT
        model = ChatOpenAI(client=client.chat.completions, model=config.model, temperature=0)
        summaries = " ".join(
            [
                SUMMARY_TEMPLATE.format(content=doc.page_content, source=doc.metadata["source"])
                for doc in merged_index.similarity_search(config.question, k=4)
            ]
        )
        context.log.info(summaries)
        output_parser = StrOutputParser()
        chain = prompt | model | output_parser
        context.log.info(chain.invoke({"summaries": summaries, "question": config.question}))


search_index_job = define_asset_job(
    "search_index_job",
    selection="*search_index",
    partitions_def=docs_partitions_def,
)


question_job = define_asset_job(
    name="question_job",
    selection="completion",
)
