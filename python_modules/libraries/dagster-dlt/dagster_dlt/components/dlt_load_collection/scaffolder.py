import ast
import shutil
import subprocess
import textwrap
from collections.abc import Mapping
from pathlib import Path
from typing import NamedTuple, Optional

from dagster._utils import pushd
from dagster.components import Scaffolder, ScaffoldRequest, scaffold_component
from dagster.components.utils import check
from pydantic import BaseModel


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
        new_content.append(pipeline_src.replace("pipeline =", f"{load_name}_pipeline ="))
        new_content.append("")

    file_path.write_text("\n".join(new_content))


class DltScaffolderParams(BaseModel):
    source: Optional[str] = None
    destination: Optional[str] = None


DLT_INIT_FILES_TO_CLEAN_UP = [".gitignore", "requirements.txt", ".dlt"]


class DltComponentScaffolder(Scaffolder):
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return DltScaffolderParams

    def scaffold(self, request: ScaffoldRequest, params: DltScaffolderParams) -> None:
        params = params or DltScaffolderParams(source=None, destination=None)
        with pushd(str(request.target_path)):
            Path.cwd().mkdir(parents=True, exist_ok=True)
            # Given source and destination, we can use dlt init to scaffold the source
            # code and some sample pipelines and sources.
            if params.source and params.destination:
                yes = subprocess.Popen(["yes", "y"], stdout=subprocess.PIPE)
                try:
                    subprocess.call(
                        ["dlt", "init", params.source, params.destination], stdin=yes.stdout
                    )
                finally:
                    yes.kill()
                # dlt init scaffolds a Python file with some example pipelines, nested in functions
                # we extract them into top-level objects which we stash in loads.py as a sample
                examples_python_file = next(Path(".").glob("*.py"))
                pipelines_and_sources = _extract_pipelines_and_sources_from_pipeline_file(
                    examples_python_file
                )
                examples_python_file.unlink()
                for file in DLT_INIT_FILES_TO_CLEAN_UP:
                    if Path(file).is_dir():
                        shutil.rmtree(file)
                    else:
                        Path(file).unlink()
                _construct_pipeline_source_file(Path("loads.py"), pipelines_and_sources)
            elif params.source or params.destination:
                raise ValueError("Must provide neither or both of source and destination")
            else:
                Path("loads.py").write_text(
                    textwrap.dedent(
                        """
                        import dlt

                        @dlt.source
                        def my_source():
                            @dlt.resource
                            def hello_world():
                                return "hello, world!"

                            return hello_world

                        my_load_source = my_source()
                        my_load_pipeline = dlt.pipeline()
                        """
                    )
                )
                pipelines_and_sources = ParsedPipelineAndSource(
                    imports=[],
                    pipelines_and_sources={
                        "my_load": PipelineAndSource(
                            pipeline_src="pipeline = dlt.pipeline()",
                            source_src="data = my_source()",
                        )
                    },
                )

        scaffold_component(
            request=request,
            yaml_attributes={
                "loads": [
                    {
                        "source": f".loads.{load_name}_source",
                        "pipeline": f".loads.{load_name}_pipeline",
                    }
                    for load_name in pipelines_and_sources.pipelines_and_sources.keys()
                ]
            },
        )
