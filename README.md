<p align="center">
<img src="https://user-images.githubusercontent.com/609349/57987382-7e294500-7a35-11e9-9c6a-f73e0f1d3a1c.png" />
<br /><br />
<a href="https://badge.fury.io/py/dagster"><img src="https://badge.fury.io/py/dagster.svg"></>
<a href="https://coveralls.io/github/dagster-io/dagster?branch=master"><img src="https://coveralls.io/repos/github/dagster-io/dagster/badge.svg?branch=master"></a>
<a href="https://buildkite.com/dagster/dagster"><img src="https://badge.buildkite.com/888545beab829e41e5d7303db15525a2bc3b0f0e33a72759ac.svg?branch=master"></a>
<a href="https://dagster.readthedocs.io/en/master/"><img src="https://readthedocs.org/projects/dagster/badge/?version=master"></a>
</p>

# Introduction

Dagster is a system for building modern data applications.

Combining an elegant programming model and beautiful tools, Dagster allows infrastructure engineers, data engineers, and data scientists to seamlessly collaborate to process and produce the trusted, reliable data needed in today's world.

### Install

To get started:
<br />

<p align="center">
<code>pip install dagster dagit</code>
</p>
<br />
This installs two modules:
<br />
<br />

- **dagster** | The core programming model and abstraction stack; stateless, single-node,
  single-process and multi-process execution engines; and a CLI tool for driving those engines.
- **dagit** | A UI and rich development environment for Dagster, including a DAG browser, a type-aware config editor, and a streaming execution interface.
  <br/>

### Learn

Next, jump right into our [tutorial](https://dagster.readthedocs.io/en/stable/sections/tutorial/index.html), or read our [complete documentation](https://dagster.readthedocs.io). If you're actively using Dagster or have questions on getting started, we'd love to hear from you:

<br />
<p align="center">
<a href="https://join.slack.com/t/dagster/shared_invite/enQtNjEyNjkzNTA2OTkzLTI0MzdlNjU0ODVhZjQyOTMyMGM1ZDUwZDQ1YjJmYjI3YzExZGViMDI1ZDlkNTY5OThmYWVlOWM1MWVjN2I3NjU"><img src="https://user-images.githubusercontent.com/609349/63558739-f60a7e00-c502-11e9-8434-c8a95b03ce62.png" width=160px; /></a>
</p>

### Contributing

For details on contributing or running the project for development, check out our [contributing guide](https://dagster.readthedocs.io/en/stable/sections/community/contributing.html).

# Integrations

Dagster works with the tools and systems that you're already using with your data, including:

<table>
	<thead>
		<tr style="background-color: #ddd" align="center">
			<td colspan=2><b>Integration</b></td>
			<td><b>Dagster Library</b></td>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td align="center" style="border-right: 0px"><img style="vertical-align:middle"  src="https://user-images.githubusercontent.com/609349/57987547-a7e36b80-7a37-11e9-95ae-4c4de2618e87.png"></td>
			<td style="border-left: 0px"> <b>Apache Airflow</b></td>
			<td><a href="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airflow" />dagster-airflow</a><br />Allows Dagster pipelines to be scheduled and executed, either containerized or uncontainerized, as <a href="https://github.com/apache/airflow">Apache Airflow DAGs</a>.</td>
		</tr>
		<tr>
			<td align="center" style="border-right: 0px"><img style="vertical-align:middle"  src="https://user-images.githubusercontent.com/609349/57987976-5ccc5700-7a3d-11e9-9fa5-1a51299b1ccb.png"></td>
			<td style="border-left: 0px"> <b>Apache Spark</b></td>
			<td><a href="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-spark" />dagster-spark</a> &middot; <a href="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-pyspark" />dagster-pyspark</a>
			<br />Libraries for interacting with Apache Spark and Pyspark.
			</td>
		</tr>
		<tr>
			<td align="center" style="border-right: 0px"><img style="vertical-align:middle"  src="https://user-images.githubusercontent.com/609349/58348728-48f66b80-7e16-11e9-9e9f-1a0fea9a49b4.png"></td>
			<td style="border-left: 0px"> <b>Dask</b></td>
			<td><a href="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dask" />dagster-dask</a>
			<br />Provides a Dagster integration with Dask / Dask.Distributed.
			</td>
		</tr>
		<tr>
			<td align="center" style="border-right: 0px"><img style="vertical-align:middle" src="https://user-images.githubusercontent.com/609349/58349731-f36f8e00-7e18-11e9-8a2e-86e086caab66.png"></td>
			<td style="border-left: 0px"> <b>Datadog</b></td>
			<td><a href="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-datadog" />dagster-datadog</a>
			<br />Provides a Dagster resource for publishing metrics to Datadog.
			</td>
		</tr>
        <!-- Commenting out until we rebuild dagster-ge on ExpectationResult et al
        <tr>
            <td align="center" style="border-right: 0px"><img style="vertical-align:middle" src="https://user-images.githubusercontent.com/609349/58349454-3846f500-7e18-11e9-84f0-6c9c75ae9993.png"></td>
            <td style="border-left: 0px"> <b>Great Expectations</b></td>
            <td><a href="https://dagster.readthedocs.io/en/stable/sections/learn/tutorial/expectations.html" />Expectations in Dagster</a><br />
            The <a href="https://github.com/great-expectations/great_expectations">Great Expectations</a> framework is designed to promote data quality checks for data warehouses. In Dagster, expectations are a first-class citizen.
            </td>
        </tr>
	    -->
		<tr>
			<td align="center" style="border-right: 0px"><img style="vertical-align:middle" src="https://user-images.githubusercontent.com/609349/57987809-bf245800-7a3b-11e9-8905-494ed99d0852.png" />
			&nbsp;/&nbsp; <img style="vertical-align:middle" src="https://user-images.githubusercontent.com/609349/57987827-fa268b80-7a3b-11e9-8a18-b675d76c19aa.png">
			</td>
			<td style="border-left: 0px"> <b>Jupyter / Papermill</b></td>
			<td><a href="https://github.com/dagster-io/dagster/tree/master/python_modules/dagstermill" />dagstermill</a><br />Built on the <a href="https://github.com/nteract/papermill">papermill library</a>, dagstermill is meant for integrating productionized Jupyter notebooks into dagster pipelines.</td>
		</tr>
		<tr>
			<td align="center" style="border-right: 0px"><img style="vertical-align:middle"  src="https://user-images.githubusercontent.com/609349/57988016-f431aa00-7a3d-11e9-8cb6-1309d4246b27.png"></td>
			<td style="border-left: 0px"> <b>PagerDuty</b></td>
			<td><a href="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-pagerduty" />dagster-pagerduty</a>
			<br />A library for creating PagerDuty alerts from Dagster workflows.
			</td>
		</tr>
		<tr>
			<td align="center" style="border-right: 0px"><img style="vertical-align:middle" src="https://user-images.githubusercontent.com/609349/58349397-fcac2b00-7e17-11e9-900c-9ab8cf7cb64a.png"></td>
			<td style="border-left: 0px"> <b>Snowflake</b></td>
			<td><a href="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-snowflake" />dagster-snowflake</a>
			<br />A library for interacting with the Snowflake Data Warehouse.
			</td>
		</tr>
		<tr style="background-color: #ddd">
			<td colspan=2 align="center"><b>Cloud Providers</b></td>
			<td><b></b></td>
		</tr>
		<tr>
			<td align="center" style="border-right: 0px"><img style="vertical-align:middle" src="https://user-images.githubusercontent.com/609349/57987557-c2b5e000-7a37-11e9-9310-c274481a4682.png"> </td>
			<td style="border-left: 0px"><b>AWS</b></td>
			<td><a href="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws" />dagster-aws</a>
			<br />A library for interacting with Amazon Web Services. Provides integrations with S3, EMR, and (coming soon!) Redshift.
			</td>
		</tr>
		<tr>
			<td align="center" style="border-right: 0px"><img style="vertical-align:middle" src="https://user-images.githubusercontent.com/609349/57987566-f98bf600-7a37-11e9-81fa-b8ca1ea6cc1e.png"> </td>
			<td style="border-left: 0px"><b>GCP</b></td>
			<td><a href="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-gcp" />dagster-gcp</a>
			<br />A library for interacting with Google Cloud Platform. Provides integrations with BigQuery and Cloud Dataproc.
			</td>
		</tr>
	</tbody>
</table>

This list is growing as we are actively building more integrations, and we welcome contributions!

# Example Projects

Several example projects are provided under the examples folder demonstrating how to use Dagster, including:

1. [**examples/airline-demo**](https://github.com/dagster-io/dagster/tree/master/examples/dagster_examples/airline_demo): A substantial demo project illustrating how these tools can be used together to manage a realistic data pipeline.
2. [**examples/event-pipeline-demo**](https://github.com/dagster-io/dagster/tree/master/examples/dagster_examples/event_pipeline_demo): An example illustrating a typical web event processing pipeline with S3, Scala Spark, and Snowflake.
