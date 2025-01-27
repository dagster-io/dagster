import io
import os
import pathlib
import tempfile
import zipfile

import requests
from langchain.docstore.document import Document


def get_wiki_data(title, first_paragraph_only):
    url = f"https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&explaintext=1&titles={title}"
    if first_paragraph_only:
        url += "&exintro=1"
    data = requests.get(url).json()
    return Document(
        page_content=next(iter(data["query"]["pages"].values()))["extract"],
        metadata={"source": f"https://en.wikipedia.org/wiki/{title}"},
    )


def get_github_docs(repo_owner, repo_name, category, archive_name="master"):
    with tempfile.TemporaryDirectory() as d:
        # The archive name can be a branch, tag or commit.
        r = requests.get(f"https://github.com/{repo_owner}/{repo_name}/archive/{archive_name}.zip")
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(d)
        root_path = pathlib.Path(os.path.join(d, f"{repo_name}-{archive_name}"))
        docs_path = root_path.joinpath("docs/content", category)
        markdown_files = list(docs_path.glob("*.md*")) + list(docs_path.glob("*/*.md*"))
        for markdown_file in markdown_files:
            with open(markdown_file) as f:
                relative_path = markdown_file.relative_to(root_path)
                github_url = f"https://github.com/{repo_owner}/{repo_name}/blob/{archive_name}/{relative_path}"
                yield Document(page_content=f.read(), metadata={"source": github_url})
