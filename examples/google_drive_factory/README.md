# Dagster Asset Factory Example

This example demonstrates how to use Dagster's asset factories to load data from Google Drive into your data platform. The example showcases reading different RDC Inventory Core Metrics data (Country, County, Metro, State, and Zip level histories) using a standardized pattern.

![Project asset lineage](./lineage.svg)

## Features used

- [Asset Factories](https://docs.dagster.io/guides/build/assets/creating-asset-factories)
- [Sensors](https://docs.dagster.io/guides/automate/sensors/)
- Authenticating with Google Cloud Platform.
- Integration with Google Drive using service account authentication
- Consistent ingestion pattern across multiple data sources

## Getting started

### Environment Setup

Ensure the following environments have been populated in your `.env` file. Start by copying the
template.

```
cp .env.example .env
```

And then populate the fields.

### Development

Install the project dependencies:

    pip install -e ".[dev]"

Start Dagster:

    DAGSTER_HOME=$(pwd) dagster dev

### Google Drive Setup

The csvs used in this demo can be found on this [site](https://www.realtor.com/research/data/)

1. Create a new project in the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the Google Drive API for your project.
3. Create Service account credentials and download the JSON key file. and save in enviroment variable
4. Share the Google Drive folder with the service account email address.
