# sphinx-mdx-builder
Generate MDX files from Sphinx

## Configuration

The extension supports the following configuration options:

| Name                   | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| `mdx_file_suffix`      | File suffix for generated files (default: `.mdx`)            |
| `mdx_link_suffix`      | Suffix for links (default: same as `mdx_file_suffix`)        |
| `mdx_file_transform`   | Function to transform docname to filename                    |
| `mdx_link_transform`   | Function to transform docname to linkname                    |
| `mdx_title_suffix`     | String to append to title in frontmatter                     |
| `mdx_title_meta`       | String to append to title in title_meta frontmatter          |
| `mdx_description_meta` | String to append to title in description frontmatter         |
| `mdx_max_line_width`   | Maximum line width for wrapped text (default: 120 characters) |
| `mdx_github_url`       | Base URL for GitHub source links (default: "https://github.com/dagster-io/dagster/blob/master") |
| `mdx_show_source_links`| Whether to show source links (default: True)                 |
