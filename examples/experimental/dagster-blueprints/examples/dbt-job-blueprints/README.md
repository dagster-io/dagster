## Example: writing a custom blueprint type for defining jobs from dbt selections

Imagine that analytics engineers in your organization want to be able to easily create executable dbt selections.

Ideally, all they need to write to set up one of these is:

```yaml
- type: dbt_select_job
  name: marketing_models
  select: "tag:marketing"
```

Custom blueprint types can help with this. Using them involves two kinds of files:

- The YAML files themselves, which contain blobs that look like the above. E.g. [dbt_job_blueprints/dbt_jobs.yaml](dbt_job_blueprints/dbt_jobs.yaml).
- Python code that defines our custom blueprint type and uses it to load these YAML files into Dagster definitions. This is located in the [dbt_job_blueprints/definitions.py](dbt_job_blueprints/definitions.py) file.

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
