from collections.abc import Mapping
from os import getenv
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader


class JinjaTemplateLoader:
    """Reads and render a file with jinja2 templating support and provide additional templating functionality.

    Ref: https://jinja.palletsprojects.com/en/stable/

    In addition to the built-in global functions and filters, this class provides the following:

    Custom jinja2 global function(s):
    - get_env(name: str, default: str = "") -> str
      Get environment variable if present or return a default value.

    Custom jinja2 filter(s):
    - to_yaml(input: Any, **kwargs) -> str
      Renders a value into its yaml representation.
    """

    @staticmethod
    def to_yaml(value: Any, **kwargs) -> str:
        return yaml.dump(value, **kwargs)

    @staticmethod
    def get_env(name: str, default: str = "") -> str:
        return getenv(name, default)

    def render(self, filepath: str, context: Mapping[str, Any]) -> str:
        path = Path(filepath)
        template_path = path.resolve().parent
        filename = path.name

        env = Environment(loader=FileSystemLoader(template_path))
        env.filters["to_yaml"] = self.to_yaml
        env.globals["get_env"] = self.get_env
        template = env.get_template(filename)
        return template.render(context)
