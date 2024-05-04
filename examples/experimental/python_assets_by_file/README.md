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
* We have also just written an asset factory (`HelloWorldProjectScript` serves that purpose here) without dynamically generating decorated functions. I think the ergonomics are much better here.

## Building the graph

Now we want to build an asset graph. For that we need dependencies. First let's create a second asset file `asset_two.py`:

```python
from dagster_pipes import open_dagster_pipes


def main(pipes) -> None:
    pipes.log.info("Hello from asset two.")


if __name__ == "__main__":
    with open_dagster_pipes() as pipes:
        main(pipes)
```

Now we need to tell the system about this dependency. We do that via a `manifest file`, which is a yaml file with the same name as the script in the same group folder.

```yaml
deps:
  - group_a/asset_one
```

Now reload your definitions and you should see a dependency graph:

![Screenshot 2024-05-04 at 2 48 13 PM](https://github.com/dagster-io/dagster/assets/28738937/371ea9d3-82a4-47e5-8192-f3ddad48af84)

You can also add tags, metadata, and other attributes via the manifest.

### Commentary on graph construction

Just a few things to note:

* A stakeholder can add themselves to the asset graph via a manifest without touching Python.
* This could easily plug into any tooling we create for the YAML DSL for typeaheads etc.
* Dependencies must be fully qualified (no asset key prefixes or anything) and it parses forward slashes, which is much more convenient than arrays of strings.
* The asset key by default is `{group_name}/{asset_name}`

## Customizing script and asset creation

As a data engineer you will want to customize this for your stakeholders. Pipes Projects provide pluggability points to do that easily, allowing your stakeholders to write standalone python scripts and yaml only, but allowing you to programmaticaly control the create of asset definitions.

For example, let's imagine that we wanted to automatically set the "kind" tag to be Python and, for every asset, make the default owner "team:foobar" if manifest did not specify an owner. But we decided that an asset author is allowed to completely override the field, rather than merge.

"Kinds" are attached to scripts, not assets. We have to create a new class that inherits from `PipesScriptManifest` and customize the tags behavior:

```python
class HelloWorldProjectScriptManifest(PipesScriptManifest):
    @property
    def tags(self) -> dict:
        # makes the kind tag "python" if it doesn't exist. User can override with their
        # own kind tag in the manifest
        return {**{"kind": "python"}, **super().tags}
```

Then you need to inform the `HelloWorldProjectScript` class to use that manifest type. To do this you have to override the `script_manifest_class` class method:

```python
class HelloWorldProjectScript(PipesScript):
    @classmethod
    def script_manifest_class(cls) -> Type:
        return HelloWorldProjectScriptManifest
```

Next we want to do a similar thing at the asset level. For that we override a `PipesAssetManifest`, and in similar fashion, override a class method in our `HelloWorldProjectScript` class.

```python
class HelloWorldProjectAssetManifest(PipesAssetManifest):
    @property
    def owners(self) -> list:
        owners_from_file = super().owners
        if not owners_from_file:
            return ["team:foobar"]
        return owners_from_file

class HelloWorldProjectScript(PipesScript):
    @classmethod
    def asset_manifest_class(cls) -> Type:
        return HelloWorldProjectAssetManifest
    ...
```

## Multiple assets in a single script

TODO


## Future work

* Deployment and Branch Deployment Management: A structure like this is highly amenable to tooling support for deployment. Imagine the ability to have a command line utility that invokes user-defined functions that script deployment of code. That script could have the branch name in context. Imagine moving code into a well-known spot in databricks or another hosted runtime. We could invoke that function on startup in dagster dev, during branch deployment creation, or any number of scenarios. The idea here is that the we have just a little support for shipping the python code the stakeholder writes into an environment they can invoke via the pipes client.
 
 
## Deployment
