## Example: writing a custom blueprint type to simplify remote CSV -> warehouse ingestion

Imagine that analytics engineers in your organization often need to work with data hosted on the internet. You want to make it easy for them to develop syncs that bring CSV files from the internet into your data warehouse.

Ideally, all they need to write to set up a sync is this:

```yaml
type: curl_asset
table_name: customers
csv_url: https://somewebsite.com/customers.csv
```

Custom blueprint types can help with this. Using them involves two kinds of files:

- The YAML files themselves, which contain blobs that look like the above. E.g. [custom_blueprints/curl_assets/customers.yaml](custom_blueprints/curl_assets/customers.yaml).
- Python code that defines our custom blueprint type and uses it to load these YAML files into Dagster definitions. This is located in the [custom_blueprints/definitions.py](custom_blueprints/definitions.py) file.

### Try it out

Make sure the blueprints library is installed, using the instructions [here](../../README.md#install).

Install the example:

```python
pip install -e .
```

Launch Dagster to see the definitions loaded from the blueprints:

```bash

dagster dev
```

Print out the JSON schema for the blueprints:

```bash
dagster-blueprints print-schema
```

If you use [VS Code](https://code.visualstudio.com/) for editing code, configure VS Code to associate the YAML files in the [custom_blueprints/curl_assets/](custom_blueprints/curl_assets/) with the blueprint schema that's used to interpret them. This will provide typeahead and type checking when editing these files.

```bash
dagster-blueprints configure-vscode
```
