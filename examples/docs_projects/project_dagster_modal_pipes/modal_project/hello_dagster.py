"""Simple demonstration of using Dagster from Modal.

modal run modal/hello_world.py

"""

import logging

import modal

app = modal.App("example-hello-world")


@app.function()
def f(identifier):
    logging.info(identifier)


@app.local_entrypoint()
def main():
    import os

    from dagster_pipes import PipesContext, open_dagster_pipes

    with open_dagster_pipes():
        context = PipesContext.get()
        context.log.info(context.extras.get("audio_file_path"))
        context.log.info(os.environ.get("CLOUDFLARE_R2_ACCESS_KEY_ID"))
        context.log.info(f"Processing static partition {context.partition_key}")
        f.remote(context.partition_key)
