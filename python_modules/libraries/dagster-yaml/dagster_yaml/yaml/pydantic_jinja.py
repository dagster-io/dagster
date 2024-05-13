from collections import ChainMap
from typing import Any, Optional

from pydantic import RootModel

from dagster_yaml.yaml.object_mapping import HasObjectMappingContext, ObjectMappingContext


def render_jinja_str(
    template: str,
    object_mapping_context: Optional[ObjectMappingContext],
    context: dict[str, Any],
    include_env: bool,
) -> str:
    """Render a Jinja template string with the provided context.

    This function uses the Jinja2 template engine to render the input `template` string with the
    given `context`. If an `object_mapping_context` is provided, it will be used to set the Jinja
    environment's file loader, which allows for loading included templates relative to the source
    file.

    The `include_env` parameter determines whether the environment variables should be included in
    the Jinja context.

    Args:
        template (str): The Jinja template string to be rendered.
            object_mapping_context (Optional[ObjectMappingContext]): The context information for the
            object being rendered, which is used to set the Jinja environment's file loader.
        context (dict[str, Any]): The context dictionary to be used for rendering the Jinja
            template.
        include_env (bool): Whether to include the environment variables in the Jinja context.

    Returns:
        str: The rendered Jinja template string.
    """
    from pathlib import Path

    from jinja2 import Environment, FileSystemLoader, Template

    loader = None
    lineno = -1
    filename = "<string>"

    if object_mapping_context is not None and object_mapping_context.source_position is not None:
        lineno = object_mapping_context.source_position.start.line
        filename = object_mapping_context.source_position.filename
        loader = FileSystemLoader(searchpath=str(Path(filename).absolute().parent))
    jinja_env = Environment(
        loader=loader,
    )
    context_stack = [context]
    if include_env:
        import os

        context_stack.append({"env": os.getenv})

    gs = jinja_env.make_globals(ChainMap(*context_stack))
    blank_lines = "\n" * (lineno + 1)
    rendered = Template.from_code(
        jinja_env,
        jinja_env.compile(blank_lines + template, filename=filename),
        gs,
    ).render()[len(blank_lines) :]
    return rendered


class JinjaStr(HasObjectMappingContext, RootModel[str]):
    root: str

    @property
    def template(self) -> str:
        return self.root

    def render(self, context: dict[str, Any] = {}, include_env: bool = True) -> str:
        return render_jinja_str(self.template, self._object_mapping_context, context, include_env)


class OptionalJinjaStr(HasObjectMappingContext, RootModel[Optional[str]]):
    root: Optional[str]

    @property
    def template(self) -> Optional[str]:
        return self.root

    def with_default(self, default: str) -> JinjaStr:
        if self.root is not None:
            return JinjaStr(self.root)
        else:
            return JinjaStr(default)

    def render(self, context: dict[str, Any] = {}, include_env: bool = True) -> Optional[str]:
        if self.template is None:
            return None

        return render_jinja_str(self.template, self._object_mapping_context, context, include_env)


JinjaStrNone = OptionalJinjaStr(None)
