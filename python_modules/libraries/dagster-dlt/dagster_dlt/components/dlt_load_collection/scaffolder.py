import ast
import shutil
import subprocess
import textwrap
from collections.abc import Mapping
from pathlib import Path
from typing import NamedTuple, Optional

from dagster import Scaffolder, scaffold_component
from dagster._utils import pushd
from dagster.components.scaffold.scaffold import ScaffoldRequest
from dagster.components.utils import check
from pydantic import BaseModel


def _format_file_if_ruff_installed(file_path: Path) -> None:
    if shutil.which("ruff"):
        subprocess.run(["ruff", "format", file_path], check=False)


class PipelineAndSource(NamedTuple):
    pipeline_src: str
    source_src: str


class ParsedPipelineAndSource(NamedTuple):
    imports: list[str]
    pipelines_and_sources: Mapping[str, PipelineAndSource]


def _extract_pipeline_and_source_from_init_file(
    node: ast.FunctionDef,
) -> PipelineAndSource:
    """Given a function body AST node, extracts the source code for the
    local Pipeline and DltSource objects.
    """
    pipeline_src = None
    source_src = None

    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                var_name = target.id
                if var_name == "pipeline":
                    pipeline_src = ast.unparse(stmt)
                elif var_name == "data":
                    source_src = ast.unparse(stmt)

    return PipelineAndSource(check.not_none(pipeline_src), check.not_none(source_src))


def _extract_pipelines_and_sources_from_pipeline_file(
    file_path: Path,
) -> ParsedPipelineAndSource:
    """Process a Python file and generate a new file with pipeline and data definitions."""
    imports = []
    pipelines_and_sources = {}
    source = file_path.read_text()
    tree = ast.parse(source)

    # Create new file content
    new_content = []
    new_content.append('"""Generated pipeline and data definitions."""\n')

    # Add imports from original file
    for node in tree.body:
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            imports.append(ast.unparse(node).replace("from ", "from ."))

    # Process each function
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            pipelines_and_sources[node.name.removeprefix("load_")] = (
                _extract_pipeline_and_source_from_init_file(node)
            )

    return ParsedPipelineAndSource(imports, pipelines_and_sources)


def _process_pipeline(src: str) -> str:
    return src.replace(", dev_mode=True", "")


def _construct_pipeline_source_file(
    file_path: Path,
    parsed_pipeline_and_source: ParsedPipelineAndSource,
) -> None:
    """Construct a new pipeline source file from a set of pipeline and source definitions."""
    new_content = []
    for import_line in parsed_pipeline_and_source.imports:
        new_content.append(import_line)

    new_content.append("\n")

    for load_name, (
        pipeline_src,
        source_src,
    ) in parsed_pipeline_and_source.pipelines_and_sources.items():
        new_content.append(source_src.replace("data =", f"{load_name}_source ="))
        new_content.append(
            _process_pipeline(pipeline_src).replace("pipeline =", f"{load_name}_pipeline =")
        )
        new_content.append("")

    file_path.write_text("\n".join(new_content))


class DltScaffolderParams(BaseModel):
    source: Optional[str] = None
    destination: Optional[str] = None


DLT_INIT_FILES_TO_CLEAN_UP = [".gitignore", "requirements.txt", ".dlt"]


class DltLoadCollectionScaffolder(Scaffolder[DltScaffolderParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[DltScaffolderParams]:
        return DltScaffolderParams

    def scaffold(self, request: ScaffoldRequest[DltScaffolderParams]) -> None:
        with pushd(str(request.target_path)):
            Path.cwd().mkdir(parents=True, exist_ok=True)
            # Given source and destination, we can use dlt init to scaffold the source
            # code and some sample pipelines and sources.
            if request.params and request.params.source and request.params.destination:
                yes = subprocess.Popen(["yes", "y"], stdout=subprocess.PIPE)
                try:
                    subprocess.check_call(
                        ["dlt", "init", request.params.source, request.params.destination],
                        stdin=yes.stdout,
                    )
                finally:
                    yes.kill()
                # dlt init scaffolds a Python file with some example pipelines, nested in functions
                # we extract them into top-level objects which we stash in loads.py as a sample
                examples_python_file = next(Path(".").glob("*.py"))
                examples_python_file.unlink()
                for file in DLT_INIT_FILES_TO_CLEAN_UP:
                    if Path(file).is_dir():
                        shutil.rmtree(file)
                    else:
                        Path(file).unlink()
            elif request.params and (request.params.source or request.params.destination):
                raise ValueError("Must provide neither or both of source and destination")

            Path("loads.py").write_text(
                textwrap.dedent(
                    """
                    import dlt

                    @dlt.source
                    def my_source():
                        @dlt.resource
                        def hello_world():
                            yield "hello, world!"

                        return hello_world

                    my_load_source = my_source()
                    my_load_pipeline = dlt.pipeline({destination})
                    """
                ).format(
                    destination=f'destination="{request.params.destination}"'
                    if request.params and request.params.destination
                    else "",
                )
            )

            _format_file_if_ruff_installed(Path("loads.py"))

        scaffold_component(
            request=request,
            yaml_attributes={
                "loads": [
                    {
                        "source": ".loads.my_load_source",
                        "pipeline": ".loads.my_load_pipeline",
                    }
                ]
            },
        )
