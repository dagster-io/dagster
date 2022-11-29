# PyData Dagster + Noteable demo workshop

This example project will be used at PyData for the Dagster and Noteable workshop.

The top level folder (`tutorial_notebook_assets`) contains two separate Dagster projects. `tutorial_finished` contains the completed version of the demo and can be used for reference during the workshop. `tutorial_template` contains a skeleton project that we will complete during the workshop. At the end of the session `tutorial_template` should be a duplicate of `tutorial_finished`.


## Workshop steps

### Environment setup

We recommend using GitPod to create a fresh Python environment for this workshop.
* https://www.gitpod.new/ and sign in with GitHub/GitLab/BitBucket

Then in your new GitPod environment, run the following commands:

```bash
$ pip install dagster
$ dagster project from-example --name dagster-noteable-demo --example tutorial_notebook_assets
$ cd dagster-noteable-demo
$ pip install -e “.[dev]”
```

### File structure
The code downloaded for this demo contains two Dagster projects. The `tutorial_finished`
folder contains a completed version of the project. `tutorial_template` contains skeleton code that we'll be filling out as part of the workshop. To keep things simple and (hopefully) bug free, most of the "coding" we'll be doing is uncommenting code snippets.

### Important files for this workshop
The two most important files for this workshop are
`tutorial_template/notebooks/iris-kmeans.ipynb`
* this file contains the Jupyter notebook we'll be working with
`tutorial_template/assets/__init__.py`
* this file is where we will be creating our Dagster assets
* when you open this file, you should see a lot of commented out code

### The Jupyter notebook

Take a quick skim through the Jupyter notebook to familiarize yourself with the contents. The most important cell to note is the cell that downloads the iris dataset

### Create a Dagster asset from a Jupyter notebook

First, we will create a Dagster asset for our notebook. In `tutorial_template/assets/__init__.py`
create the asset by uncommenting the code labeled `TODO 1`

```python
iris_kmeans_jupyter_notebook = define_dagstermill_asset(
    name="iris_kmeans_jupyter",
    notebook_path=file_relative_path(__file__, "../notebooks/iris-kmeans.ipynb"),
    # ins={"iris": AssetIn("iris_dataset")}, # this code to remain commented until TODO 3
    group_name="template_tutorial"
)
```

### Materialize the notebook asset
Launch Dagit (Dagster's UI)

```bash
$ dagit
```
and and navigate to http://localhost:3000/. Feel free to look around at some of the pages available.

To materialize (execute) our notebook asset, navigate to the asset graph by clicking the hamburger menu icon in the top left corner. Then selecting the `template_tutorial` Asset Group in the `template_tutorial` repository. The `finished_tutorial` repository has all of the assets in the finished project, so feel free to take a quick look at those to get a sneak peak for what's next.

In the asset graph for the `template_tutorial` Asset Group, click the Materialize button in the top right to materialize the notebook.
An alert will pop up with a "View" button. Click this button to see the logs for the notebook execution.

### Create an iris dataset asset
At this point your notebook should materialize successfully, but we are still fetching the iris dataset within the notebook. We want to factor out the iris dataset so that it is it's own asset. In `tutorial_template/assets/__init__.py` uncomment the code with the label `TODO 2` to create an asset for the iris dataset.

```python
@asset(
    group_name="template_tutorial"
)
def iris_dataset():
    return pd.read_csv(
        "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        names=[
            "Sepal length (cm)",
            "Sepal width (cm)",
            "Petal length (cm)",
            "Petal width (cm)",
            "Species",
        ],
    )
```

You will also need to tell Dagster to use the iris dataset asset in the iris-kmeans notebook.
Update your notebook asset with the `ins` parameter by uncommenting the code labeled `TODO 3`

```python
iris_kmeans_jupyter_notebook = define_dagstermill_asset(
    name="iris_kmeans_jupyter",
    notebook_path=file_relative_path(__file__, "../notebooks/iris-kmeans.ipynb"),
    ins={"iris": AssetIn("iris_dataset")},
    group_name="template_tutorial"
)
```

You'll also need to modify the notebook slightly so that dagster can inject the iris asset as an input.
In `tutorial_template/notebooks/iris-kmeans.ipynb`, cut the code to download the iris dataset and put it in the cell tagged with the parameters tag (it also contains a comment specifying that it is tagged)

```python
# this cell has been tagged with "parameters"
```

### Materialize the assets
Go back to the asset graph in Dagit, and click "Reload definitions". You should see a new asset appear
for your iris dataset

Click "Materialize" to materialize the iris dataset and the notebook

### Using a Noteable notebook with Dagster
Now we're going to use a Noteable notebook in Dagster.
### Sign up for Noteable
The first thing you'll need to do is make an account with Noteable. Navigate to https://noteable.io/ and sign up for an account.

### Upload your notebook to Noteable
If you're using GitPod, download your Jupyter notebook by right-clicking the notebook file in the left sidebar and clicking "Download".

In Noteable, navigate to your "Space" by clicking the Noteable logo in the top left corner. You should see a project labeled "My First Project". Click into this project, then click the upload button to upload your notebook. Then you can open your notebook in a new tab and take a look

### Get your Noteable API token
You'll also need an API token from Noteable so that your code can talk to Noteable. To get your API token, click on your profile in the top right corner, then click Settings > API Tokens. Then you can generate a new token and copy the value.

Navigate back to the terminal where you are running Dagit. Terminate the dagit process and create an environment variable for your Noteable API token

```bash
$ export NOTEABLE_TOKEN=<your noteable token>
```

Then restart Dagit

```bash
$ dagit
```

### Create a Dagster asset for the Noteable notebook
Now we'll create a new asset for the Noteable notebook. In `tutorial_template/assets/__init__.py` uncomment the code labeled `TODO 5`

```python
notebook_id = "<your-noteable-notebook-id>"
iris_kmeans_noteable_notebook = define_noteable_dagster_asset(
    name="iris_kmeans_noteable",
    notebook_id=notebook_id,
    ins={"iris": AssetIn("iris_dataset")},
    group_name="template_tutorial"
)
```

We need to get our Noteable notebook ID to complete this code snippet. Navigate back to your Noteable notebook. In the address bar, the URL will have a sequence of numbers and letters. This is your notebook ID. Copy this value and set it for the variable `notebook_id`

### Materialize the notebook asset
Navigate back to the asset graph in Dagit and click "Reload definitions". You should see a new asset appear for your Noteable notebook.
To materialize just the iris dataset asset and the Noteable notebook asset, hold the Shift key and click the iris dataset asset and the Noteable notebook asset. Then click the materialize button. Click the View button when it appears and watch the logs. You'll see a link to a Noteable notebook printed in the logs. If you click this link you can watch your notebook execute in real time!

### Live debugging
In order to debug, we must first make a bug. In your original (not executed) Noteable notebook, scroll down a few cells and create a new cell. In this cell, raise an exception:

```python
raise Exception("oh no!")
```

Navigate back to dagit, and select the Noteable notebook asset. Click the Materialize button, then click the View button.

As you watch the logs, wait for the run to fail. Once you see the failure, click on the link to the executing Noteable notebook that was printed in the logs. Now you are still in a live notebook. The cells before the failure are still executed so you can use any values that were previously computed to debug your error. Go ahead and fix the error by commenting out the exception or deleting the cell. Then execute the remaining cells in the notebook.


## Conclusion
Congratulations! You've completed the workshop! If you have any follow up questions, please ask the workshop moderators, or reach out to us on the [Dagster Slack](https://dagster.slack.com)