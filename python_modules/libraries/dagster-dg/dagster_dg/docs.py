import tempfile
import webbrowser

import markdown

from dagster_dg.context import RemoteComponentType


def render_markdown_in_browser(markdown_content: str) -> None:
    # Convert the markdown string to HTML
    html_content = markdown.markdown(markdown_content)

    # Add basic HTML structure
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Markdown Preview</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
        temp_file.write(full_html.encode("utf-8"))
        temp_file_path = temp_file.name

    # Open the temporary file in the default web browser
    webbrowser.open(f"file://{temp_file_path}")


def markdown_for_component_type(component_type_metadata: RemoteComponentType) -> str:
    return f"""
## Component: `{component_type_metadata.package}`.`{component_type_metadata.name}`
 
### Description: 
`{component_type_metadata.description}`
                               """
