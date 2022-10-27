# Assets with Notebooks Example

This is an example of how to use the Software-Defined Asset APIs to run notebooks. The example demonstrates loading and
executing a Jupyter notebook as a Dagster asset. Additionally, Dagster can be used to run Noteable notebooks. We cover this
as an additional part of this example.


## Getting started

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example assets_notebook
```

To install this example and its Python dependencies, run:

```bash
cd my-dagster-project
pip install -e ".[dev]"
```

Once you've done this, you can run:

```
dagit
```

to view this example in Dagster's UI, Dagit.

By default only the repository with a Jupyter notebook-backed asset will be loaded into Dagit. You can find
the source code for the assets in `assets_notebook/assets/data_assets.py` and `assets_notebook/assets/jupyter_assets.py`. In order to materialize the assets, you will need to have a Jupyter kernel running
```
python -m ipykernel install --user --name=dagster
```



## Noteable notebooks

If you would like to work with a Noteable notebook in this example, you will need to complete the following setup:
1. Create a Noteable account at https://noteable.io/
2. Create a new notebook in your Noteable account (you can name it whatever you'd like) and upload the contents of the notebook in this project by clicking File > Import and upload the notebook at `assets_notebook/notebooks/iris-kmeans.ipynb`.
3. In `assets_notebook/assets/noteable_assets.py` replace the value of `notebook_id` with the ID of your newly created notebook. You can find the ID in the URL of the notebook. For example if your notebook URL is `https://app.noteable.io/f/12345678-abcd-1234-abcd-123456789012/dagster_example.ipynb`, the ID is `12345678-abcd-1234-abcd-123456789012`
4. Generate an Noteable API token by going to your profile > Settings > API Tokens and generating a new token.
5. Create an environment variable `NOTEABLE_TOKEN` with the value of the token from step 4.
6. In `workspace.yaml` uncomment the indicated lines to load the Noteable repository.

Now you can run `dagit` and see a repository `noteable_repository` has been loaded into Dagit along with `jupyter_repository`. This repository also contains a job `ping_noteable` that you can run to ensure that your API token has been set correctly. You can materialize the assets in `noteable_repository` and watch your Noteable notebook execute in real time. The source code for the assets in this repository is in `assets_notebook/assets/data_assets.py` and `assets_notebook/assets/noteable_assets.py`
