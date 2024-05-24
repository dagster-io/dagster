# Requests

This directory simulates a request system in the sensors portion of Dagster University. By creating a "request" file in this directory, your Dagster project will automatically pick up the request and run the pipeline with the parameters specified in the request.

The pipeline stores the results in the `data/results` directory.

## How it Works

Create a new request by adding a file to this directory. The file has to be a valid JSON file with the following fields:

- `start_date`: The beginning of the range of inquiry, in the format `YYYY-MM-DD`
- `end_date`: The end of the range of inquiry, in the format `YYYY-MM-DD`
- `borough`: The borough to query; one of `Manhattan`, `Brooklyn`, `Queens`, `Bronx`, or `Staten Island`

Here is a sample request:

```json
{
  "start_date": "2023-01-10",
  "end_date": "2023-01-25",
  "borough": "Staten Island"
}
```

Assuming that the file is named `january-staten-island.json`, the result of the pipeline will be stored in `data/results/january-staten-island.json`.
