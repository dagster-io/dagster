# Pipes Projects™

Pipes projects is a way to structure your Dagster projects if you want to execute external scripts with Dagster Pipes. It has an opinionated file layout scheme. The explicit goal of this approach is to allow for contributors to add and contribute to python-based assets in Dagster without interact with the core `dagster` library or program against it. They shouldn't even need to have a python environment that includes it if they rely on branch deployments.

## Hello world asset

To get started you'll need to create a `definitions.py` file and a `defs` folder. 

* `definitions.py` is the file that actually creates a `Definitions` object. This is file is typically managed by the owner of the data platform and someone who interacts and knows Dagster well. 
* `defs` is the folder that contains all the business logic for your assets. The code in `definitions.py` introspects `defs` to build the asset graph.

`definitions.py`:
```python 
from dagster import AssetExecutionContext, Definitions, PipesSubprocessClient
from dagster._core.pipes.project import PipesScript


class HelloWorldProjectScript(PipesScript):
    def execute(self, context: AssetExecutionContext, subprocess_client: PipesSubprocessClient):
        command = [self.python_executable_path, self.python_script_path]
        return subprocess_client.run(context=context, command=command).get_results()


defs = Definitions(
    assets=HelloWorldProjectScript.make_pipes_project_defs(),
    resources={"subprocess_client": PipesSubprocessClient()},
)
```

This is a vanilla Dagster `Definitions` object, build with a special factory function, `make_pipes_project_defs`.

Next you need to make a `defs` folder. The first level of a `defs` folder defines the groups in a code location. Assets are defined within groups.

So in this case we make a folder `defs` and then `group_a`. Finally we make a Python that contains the business logic for the asset at `defs/group_a/asset_one.py`.

```python
from dagster_pipes import open_dagster_pipes

def main(pipes) -> None:
    pipes.log.info("Hello")

if __name__ == "__main__":
    with open_dagster_pipes() as pipes:
        main(pipes)
```

With these two files in place we can load them in Dagster UI with `dagster dev -f definitions.py`.

![Screenshot 2024-05-04 at 2 23 04 PM](https://github.com/dagster-io/dagster/assets/28738937/6244402d-35ca-41fa-bcdc-a81dcac56876)

Note that the folder you made, `group_a`, corresponds to a group in the left nav. Similarly the file you created `asset_one.py`, creates an asset called `asset_one`. If you click on the asset, more information appears:

![Screenshot 2024-05-04 at 2 24 36 PM](https://github.com/dagster-io/dagster/assets/28738937/9a01adaf-df4d-4bcc-9c8f-0c07c24d3c06)

The entire contents of the python file are included in the description for your convenience. In addition, you'll note that there is a "Code Version." Dagster uses this to detect if your code has changed and requires recomputation to keep your assets up-to-date. It is just a hash computed from the contents of your pipes script. We'll come back to that later.

Next you can click on asset and materialize it. You are off to the races!

### Commentary on Hello World

During this README I'm going to interrrupt it with commentary to note decisions made for users.

* We are heavily opting the user into groups here. There a couple reasons here.
    * Want make groups "heavier" here and make them a function of filesystem layout. The "default" group would have confused that mental model considerably, so I just made it impossible to create an asset without a group. We could find lighterweight solutions here, but I think the outcome is pretty reasonable.
    * By default, this system incorporates group name into the asset key. In general Project Pipes 1) will never introduce the concept of asset prefix 2) will assume that groups are just incorporate into the asset key and 3) let the user opt into explicit asset key management if they want to do so.
* Forcing a file-per-script gets us a bunch of a stuff for free. Two of them are right up front: rendering the python code in the UI and usage of the code versioning system.

## Building the graph



## TODO Discussions

* Groups versus asset prefixes.

