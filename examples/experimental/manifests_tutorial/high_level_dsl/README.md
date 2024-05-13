# Preamble/Introduction

This builds on https://github.com/dagster-io/internal/discussions/9601.

High-level a few changes:

* A new name, Dagster Manifests, rather than a cute code name.
  * This is also my proposed re-framing for the dagster-yaml project.
  * A manifest is a serialized representation of definitions.
  * It is not a new word in the data ecosystem. Dbt has manifests that serve the same purpose and people understand that.
  * The most essential idea in this workstream is not yaml, but the ability to build definitions in a standardized way from a serializable format.
  * YAML is just a manifest frontend. In the future we might have forms-based manifest frontends.
  * Indicates a more foundational system. For example, I think we should have GraphQL/REST APIs for this subsystem, which will be a super powerful layer for tool building
* In terms the yaml frontend, which is very important, I have integrated the schema registration system (albiet hardcoded for the single example for simplicity) in order to learn prove to myself that it will work. It is a pretty magical experience to build custom manifest formats and then get a typeahead and better error messages for free.
* This is stacked on the AssetGraphExecutable PR (https://github.com/dagster-io/dagster/pull/21679). My conviction has only grown that an abstraction shaped like this is the path forward. Still do not have high conviction on the name. Feedback very welcome on that front.
* The core system is much more pluggable and flexible than the previous Nope prototype.
  * There is a quite generic notion of a "manifest source", which is a class that produce a top-level manifest object. Sources can be arbitrary file formats or any durable store.
  * Similarly the manifest schema format is just Pydantic. The platform owner can designed whatever they want on this front.
    * Note: because it is all backed by plain python objects it is well-supported to construct manifests programmatically for those who violently object to YAML, which I sympathize with.

I have _not_ wrtten sequence of examples where complexity builds from a hello world, but I did write an "advanced" example that demonstrates the core primitives and how flexible this is. We would build sugar and out-of-the-box solutions and sugar to craft a minimal hello world and default formats and scaffolding.
 
I also invision this as a powerful layer for standardizing integrations. Consuming a dbt integration via a manifest was quite natural.  It would even be more natural to write it if a native "AssetGraphExecutable"-style abstraction existed for that integration. 

It is important that dagster-yaml and this effort converge ASAP. The time for parallel exploration has come to an end IMO.

Next up is the tutorial written in the voice of "talking to a platform owner user of Dagster".

# Advanced Manifests Tutorial: Customizing the platform

As a platform owner you can use Manifests to build a custom platform for your stakeholders. This means you have total control of the manifest format and control over how those manifest formats translate into executables and assets. You can mix and match pre-built executables and custom executables in the same manifest format.

## Manifest Factory

Let's look at `definitions.py`. We need to define a manifest factory. 

Manifest factories determine two things:

1) Format for the manifest
2) Given an instance of that manifest, how to create a `Definitions` object.

```python
# elided other imports for brevity
from dagster._manifest.executables.subprocess import PipesSubprocessManifestExecutable
from executables.bespoke_elt import BespokeELTExecutable
from executables.dbt_manifest import DbtManifestJsonExecutable

class HighLevelDSLManifestFactory(ManifestBackedExecutableFactory[HighLevelDSLManifest]):

    @classmethod
    def executables(cls) -> List[Type[ManifestBackedExecutable]]:
        return [
            BespokeELTExecutable,
            DbtManifestJsonExecutable,
            PipesSubprocessManifestExecutable,
        ]
    ...
```


We're using the `ManifestBackedExecutableFactory` which is a light specialization of the `ManifestFactory` base class. It defines a schema with a top-level key `executables` that points to a list of executables where each entry is one of a set executable types. The user overrides the `executables` classmethod to return executable types. In this case we are using an off-the-shelf subprocess-based one, a dbt integration, and a custom integration we have built to interact with our ancient, bespoke ELT system.

## Manifest File and Schema 

```yaml
# group_a.yaml
executables:
  - kind: bespoke_elt 
    name: transform_and_load
    source: file://example/file.csv
    destination: s3://bucket/file.csv
    assets:
      - key: root_one 
      - key: root_two 
  - kind: dbt_manifest
    manifest_json_path: jaffle_shop/target/manifest.json
  - kind: subprocess
    python_script_path: scripts/some_script.py
    assets:
      - key: ml_team/downstream
        # by default in this file group name inherited from group
        # name but can override on per-asset basis
        group_name: ml_team
        deps: ["customers"]
```

This is the yaml we want your stakeholders to be able to write and modify. `dbt_manifest` and `subprocess` executable kinds already exist. Let's learn how to write a custom manifest-backed executable

By convention, custom executables live in the `executables` folder and the file is named after the `kind`. Hence `executables/bespoke_etl.py`:

First we want to write the manifest file format we want our stakeholders to use. Let's start with that interface:

```python
class BespokeELTAssetManifest(BaseModel):
    key: str

class BespokeELTExecutableManifest(BaseModel):
    kind: Literal["bespoke_elt"]
    group_name: Optional[str]
    name: str
    source: str
    destination: str
    assets: List[BespokeELTAssetManifest]
```

An executable manifest must have a kind field (this is enforced via a protocol in the type system) to work with `ManifestBackedExecutableFactory` but the rest of this is user-defined. Once you have the Pydantic class written the yaml parser and typeahead just works.

## Building a custom manifest-backed Executable

Next you'll see that the custom executable. It specifies a manifest type and then an `execute` method that is executed during a run.

```python
class BespokeELTExecutable(ManifestBackedExecutable):
    @classmethod
    def create_from_manifest(cls, manifest: BespokeELTExecutableManifest) -> "BespokeELTExecutable":
        return BespokeELTExecutable(
            manifest=manifest,
            specs=[
                AssetSpec(key=asset_key, group_name=manifest.group_name)
                for asset_key in manifest.assets.keys()
            ],
        )

    @classmethod
    def manifest_cls(cls) -> Optional[Type[ExecutableManifest]]:
        return BespokeELTExecutableManifest

    def execute(self, context: AssetGraphExecutionContext) -> AssetGraphExecutionResult:
        context.log.info("Running bespoke ELT")
        for spec in self.specs:
            context.log.info(f"Running {spec.key}")
            assert isinstance(spec, AssetSpec)  # only do assets right now
            yield MaterializeResult(asset_key=spec.key)
```

Let's go through the methods you need to implement in any subclass of `ManifestBackedExecutable`.

1. `manifest_cls`. Return the manifest type.
2. `create_from_manifest`. Given a manifest object, return an instance of the executable.
3. `execute`: Implement the `execute` method of `AssetGraphExecutable` as normal.

_Note: I bet we could get this down to two methods with generics._

Now that we have this class and imported it into `HighLevelDSLManifestFactory` we are good to go. This use can opt into this executable with `kind: bespoke_elt` in the manifest file. Pretty cool!

Now that we have our manifest factory set up,

## Manifest Source

Last let's the manifest source. We want to control the file layout. In this case we want the file name to determine the default group for any artifacts in that file:

```python
from pathlib import Path

from dagster import _check as check
from dagster._manifest.definitions import (
    ManifestSource,
)
from dagster._manifest.pydantic_yaml import load_yaml_to_pydantic
from manifest import (
    HighLevelDSLManifest,
)


class HighLevelDSLFileSystemManifestSource(ManifestSource):
    def __init__(self, path: Path):
        self.path = path

    @staticmethod
    def get_yaml_files(path: Path) -> Iterable[Path]:
        for file_path in path.iterdir():
            if file_path.suffix == ".yaml":
                yield file_path

    def get_manifest(self) -> "HighLevelDSLManifest":
        all_executables = []
        manifests_by_default_group = {}
        for yaml_file in HighLevelDSLFileSystemManifestSource.get_yaml_files(self.path):
            manifests_by_default_group[yaml_file.stem] = check.inst(
                load_yaml_to_pydantic(str(yaml_file), HighLevelDSLManifest),
                HighLevelDSLManifest,
            ).executables

        for group_name, executables in manifests_by_default_group.items():
            for executable in executables:
                if executable.group_name is None:
                    all_executables.append(executable.copy(update={"group_name": group_name}))
                else:
                    all_executables.append(executable)

        return HighLevelDSLManifest(executables=all_executables)

```

This manifest source walks a folder structure and gets every yaml file and creates a set of definitions out of them. Group name is by default the name of the file, but can be overriden.

Finally we can put it all together to create the final `Definitions` object.

```python

def make_high_level_dsl_definitions() -> Definitions:
    return HighLevelDSLManifestFactory().make_definitions(
        manifest=HighLevelDSLFileSystemManifestSource(
            path=Path(__file__).resolve().parent / Path("manifests")
        ).get_manifest(),
        resources={
            "dbt": DbtCliResource(str((Path(__file__).parent / Path("jaffle_shop")).resolve())),
            "subprocess_client": PipesSubprocessClient(),
        },
    )


defs = make_high_level_dsl_definitions()
```

By convention, manifest files go into the `manifests` folder so that is where we look. We have the source create a manifest object, pass that to the factory's `make_definition` function, and provide the appropriate resources.


# Future Directions

* Support partitioning, scheduling, and other features in this system.
* Prototype using the manifest layer to generate Airflow operators. The critical piece here is that there will be custom code to translate the yaml to the operators, rather than exposing the raw arguments to the Airflow operators.
