import pathlib
import pickle
import subprocess
import tempfile

import requests
from dagster import AssetSelection, Definitions, EnvVar, asset, define_asset_job
from dagster_openai import OpenAIResource
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS


@asset
def source_docs():
    return list(get_github_docs("dagster-io", "dagster"))


@asset
def search_index(source_docs):
    source_chunks = []
    splitter = CharacterTextSplitter(separator=" ", chunk_size=1024, chunk_overlap=0)
    for source in source_docs:
        for chunk in splitter.split_text(source.page_content):
            source_chunks.append(Document(page_content=chunk, metadata=source.metadata))
    search_index = FAISS.from_documents(source_chunks, OpenAIEmbeddings())
    with open("search_index.pickle", "wb") as f:
        pickle.dump(search_index.serialize_to_bytes(), f)


def get_wiki_data(title, first_paragraph_only):
    url = f"https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&explaintext=1&titles={title}"
    if first_paragraph_only:
        url += "&exintro=1"
    data = requests.get(url).json()
    return Document(
        page_content=next(iter(data["query"]["pages"].values()))["extract"],
        metadata={"source": f"https://en.wikipedia.org/wiki/{title}"},
    )


def get_github_docs(repo_owner, repo_name):
    with tempfile.TemporaryDirectory() as d:
        subprocess.check_call(
            f"git clone --depth 1 https://github.com/{repo_owner}/{repo_name}.git .",
            cwd=d,
            shell=True,
        )
        git_sha = (
            subprocess.check_output("git rev-parse HEAD", shell=True, cwd=d).decode("utf-8").strip()
        )
        repo_path = pathlib.Path(d)
        markdown_files = list(repo_path.glob("*/*.md")) + list(repo_path.glob("*/*.mdx"))
        for index, markdown_file in enumerate(markdown_files):
            with open(markdown_file) as f:
                relative_path = markdown_file.relative_to(repo_path)
                github_url = (
                    f"https://github.com/{repo_owner}/{repo_name}/blob/{git_sha}/{relative_path}"
                )
                yield Document(page_content=f.read(), metadata={"source": github_url})


asset_selection = AssetSelection.all()


openai_asset_job = define_asset_job(name="openai_asset_job", selection=asset_selection)


defs = Definitions(
    assets=[source_docs, search_index],
    jobs=[openai_asset_job],
    resources={
        "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
    },
)
