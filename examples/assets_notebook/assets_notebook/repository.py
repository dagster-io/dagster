import requests
import os
import json
from dagster import load_assets_from_package_module, repository, op, job

from assets_notebook.assets import iris_dataset, noteable_iris_notebook, jupyter_iris_notebook

############ Repository with an asset backed by a Jupyter notebook ############
@repository
def jupyter_repository():
    return [
        iris_dataset,
        jupyter_iris_notebook
    ]


############ Repository with an asset backed by a Noteable notebook ############

@op
def ping_noteable_op(context):
    api_token = os.environ["NOTEABLE_TOKEN"]
    domain = os.getenv("NOTEABLE_DOMAIN", "app.noteable.io")
    headers = requests.utils.default_headers()
    headers.update({"Authorization": f"Bearer {api_token}"})

    r = requests.get(
        f"https://{domain}/gate/api/spaces?limit=10&with_deleted=false", headers=headers
    )
    r.raise_for_status()
    spaces = r.json()
    context.log.info(json.dumps(spaces, indent=4))
    return spaces


@job
def ping_noteable():
    ping_noteable_op()

@repository
def noteable_repository():
    return [
        iris_dataset,
        noteable_iris_notebook,
        ping_noteable
    ]
