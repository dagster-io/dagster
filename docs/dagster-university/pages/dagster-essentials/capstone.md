---
title: 'Capstone'
module: 'dagster_essentials'
lesson: 'capstone'
---

# Capstone

Congrats on making it this far! In this section, you’ll apply what you’ve learned so far and build out your own Dagster project.

---

## Project data

The best way to apply what you’ve learned is to use your own organization’s data, but if this isn’t possible, you can use additional data from [NYC OpenData](https://opendata.cityofnewyork.us/) or [GitHub’s list of public APIs](https://github.com/public-apis/public-apis).

If using NYC OpenData, we recommend using the **311 Service Requests from 2010 to Present** dataset. The data is downloadable as a CSV and you’re welcome to view [details about it here](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9).

Whatever data you decide to use, we choose something that sparks your interest!

You can also continue to use DuckDB if needed.

---

## Project requirements

When building your own project, it should:

- Create a data pipeline using assets
- Try out one of [Dagster’s supported integrations](https://docs.dagster.io/integrations) like dbt, Fivetran, or Airbyte
- Include a resource that connects to a data source or storage
  - We provide out-of-the-box connections to most popular cloud data warehouses. However, you can turn [any Python connection or object into a resource](https://docs.dagster.io/concepts/resources#using-bare-python-objects-as-resources).
  - If you aren’t going to use company data, you can continue using DuckDB.
- Perform some transformations on the data, either using cloud compute or in-memory computations.
  - If you’re interested in using dbt, check out [our dbt integration](https://docs.dagster.io/integrations/dbt/reference#loading-dbt-models-from-a-dbt-project)!
- Partition your assets and try backfilling historical data
- Make a report using the data

---

## Getting help

If you get stuck or have questions, you can:

- Join the [Dagster Slack](https://dagster.io/community) community and ask a question in our `#ask-community` channel
- Find solutions and patterns in our [GitHub discussions](https://github.com/dagster-io/dagster/discussions)
- Check out the [Dagster Docs](https://docs.dagster.io)

---

## Share your work!

We’d love to see what you create! When you’re done, you can:

- Add the project to a public GitHub repository
- Tag us on your socials, like Twitter/X or LinkedIn! We’re `@dagster` on both platforms.
- Join the Dagster Slack community and share your work in `#dagster-showcase`
