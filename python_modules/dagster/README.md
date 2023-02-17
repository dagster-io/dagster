<p align="center">
  <!-- Note: Do not try adding the dark mode version here with the `picture` element, it will break formatting in PyPI -->
  <a target="_blank" href="https://dagster.io" style="background:none">
    <img alt="dagster logo" src="https://raw.githubusercontent.com/dagster-io/dagster/master/.github/dagster-logo-light.svg" width="auto" height="120">
  </a>
  <br /><br />
  <a target="_blank" href="https://twitter.com/dagster" style="background:none">
    <img src="https://img.shields.io/badge/twitter-dagster-blue.svg?labelColor=4F43DD&color=163B36&logo=twitter" />
  </a>
  <a target="_blank" href="https://dagster.io/slack" style="background:none">
    <img src="https://img.shields.io/badge/slack-dagster-blue.svg?labelColor=4F43DD&color=163B36&logo=slack" />
  </a>
  <a target="_blank" href="https://linkedin.com/showcase/dagster" style="background:none">
    <img src="https://img.shields.io/badge/linkedin-dagster-blue.svg?labelColor=4F43DD&color=163B36&logo=linkedin" />
  </a>
  <a target="_blank" href="https://github.com/dagster-io/dagster" style="background:none">
    <img src="https://img.shields.io/github/stars/dagster-io/dagster?labelColor=4F43DD&color=163B36&logo=github">
  </a>
  <br />
  <a target="_blank" href="https://github.com/dagster-io/dagster/blob/master/LICENSE" style="background:none">
    <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?label=license&labelColor=4F43DD&color=163B36">
  </a>
  <a target="_blank" href="https://pypi.org/project/dagster/" style="background:none">
    <img src="https://img.shields.io/pypi/v/dagster?labelColor=4F43DD&color=163B36">
  </a>
  <a target="_blank" href="https://pypi.org/project/dagster/" style="background:none">
    <img src="https://img.shields.io/pypi/pyversions/dagster?labelColor=4F43DD&color=163B36">
  </a>
</p>

# Dagster

Dagster is an orchestrator that's designed for developing and maintaining data assets, such as tables, data sets, machine learning models, and reports.

You declare functions that you want to run and the data assets that those functions produce or update. Dagster then helps you run your functions at the right time and keep your assets up-to-date.

Dagster is built to be used at every stage of the data development lifecycle - local development, unit tests, integration tests, staging environments, all the way up to production.

If you're new to Dagster, we recommend reading about its [core concepts](https://docs.dagster.io/concepts) or learning with the hands-on [tutorial](https://docs.dagster.io/tutorial).

An asset graph defined in Python:

```python
from dagster import asset
from pandas import DataFrame, read_html, get_dummies
from sklearn.linear_model import LinearRegression

@asset
def country_populations() -> DataFrame:
    df = read_html("https://tinyurl.com/mry64ebh")[0]
    df.columns = ["country", "continent", "rg", "pop2018", "pop2019", "change"]
    df["change"] = df["change"].str.rstrip("%").str.replace("−", "-").astype("float")
    return df

@asset
def continent_change_model(country_populations: DataFrame) -> LinearRegression:
    data = country_populations.dropna(subset=["change"])
    return LinearRegression().fit(
        get_dummies(data[["continent"]]), data["change"]
    )

@asset
def continent_stats(
    country_populations: DataFrame, continent_change_model: LinearRegression
) -> DataFrame:
    result = country_populations.groupby("continent").sum()
    result["pop_change_factor"] = continent_change_model.coef_
    return result
```

The graph loaded into Dagster's web UI:

<p align="center">
  <img width="478" alt="image" src="https://user-images.githubusercontent.com/654855/183537484-48dde394-91f2-4de0-9b17-a70b3e9a3823.png">
</p>

## Installation

Dagster is available on PyPI and officially supports Python 3.7+.

```bash
pip install dagster dagit
```

This installs two modules:

- **Dagster**: The core programming model.
- **Dagit**: The web interface for developing and operating Dagster jobs and assets.

## Documentation

You can find the full Dagster documentation [here](https://docs.dagster.io).

## Community

Connect with thousands of other data practitioners building with Dagster. Share knowledge, get help,
and contribute to the open-source project. To see featured material and upcoming events, check out
our [Dagster Community](https://dagster.io/community) page.

Join our community here:

- 🌟 [Star us on Github](https://github.com/dagster-io/dagster)
- 📥 [Subscribe to our Newsletter](https://dagster.io/newsletter-signup)
- 🐦 [Follow us on Twitter](https://twitter.com/dagster)
- 🕴️ [Follow us on LinkedIn](https://linkedin.com/showcase/dagster)
- 📺 [Subscribe to our YouTube channel](https://www.youtube.com/channel/UCfLnv9X8jyHTe6gJ4hVBo9Q)
- 📚 [Read our blog posts](https://dagster.io/blog)
- 👋 [Join us on Slack](https://dagster.io/slack)
- 🗃 [Browse Slack archives](https://discuss.dagster.io)
- ✏️ [Start a Github Discussion](https://github.com/dagster-io/dagster/discussions)

## Contributing

For details on contributing or running the project for development, check out our [contributing
guide](https://docs.dagster.io/community/contributing/).

## License

Dagster is [Apache 2.0 licensed](https://github.com/dagster-io/dagster/blob/master/LICENSE).
