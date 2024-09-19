import {Box, Colors, FontFamily, IconWrapper} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import csv from './kindtag-images/csv.svg';
import dag from './kindtag-images/dag.svg';
import dashboard from './kindtag-images/dashboard.svg';
import file from './kindtag-images/file.svg';
import medallion_bronze from './kindtag-images/medallion-bronze-color.svg';
import medallion_gold from './kindtag-images/medallion-gold-color.svg';
import medallion_silver from './kindtag-images/medallion-silver-color.svg';
import notebook from './kindtag-images/notebook.svg';
import pdf from './kindtag-images/pdf.svg';
import seed from './kindtag-images/seed.svg';
import sigma from './kindtag-images/sigma.svg';
import source from './kindtag-images/source.svg';
import table from './kindtag-images/table.svg';
import task from './kindtag-images/task.svg';
import airbyte from './kindtag-images/tool-airbyte-color.svg';
import airflow from './kindtag-images/tool-airflow-color.svg';
import airtable from './kindtag-images/tool-airtable-color.svg';
import atlan from './kindtag-images/tool-atlan-color.svg';
import aws from './kindtag-images/tool-aws-color.svg';
import axioma from './kindtag-images/tool-axioma-color.svg';
import azure from './kindtag-images/tool-azure-color.svg';
import azureml from './kindtag-images/tool-azureml-color.svg';
import bigquery from './kindtag-images/tool-bigquery-color.svg';
import catboost from './kindtag-images/tool-catboost-color.svg';
import celery from './kindtag-images/tool-celery-color.svg';
import census from './kindtag-images/tool-census-color.svg';
import chalk from './kindtag-images/tool-chalk-color.svg';
import claude from './kindtag-images/tool-claude-color.svg';
import collibra from './kindtag-images/tool-collibra-color.svg';
import cplus from './kindtag-images/tool-cplus-color.svg';
import csharp from './kindtag-images/tool-csharp-color.svg';
import cube from './kindtag-images/tool-cube-color.svg';
import dask from './kindtag-images/tool-dask-color.svg';
import databricks from './kindtag-images/tool-databricks-color.svg';
import datadog from './kindtag-images/tool-datadog-color.svg';
import datahub from './kindtag-images/tool-datahub-color.svg';
import dbt from './kindtag-images/tool-dbt-color.svg';
import delta_lake from './kindtag-images/tool-deltalake-color.svg';
import discord from './kindtag-images/tool-discord-color.svg';
import dlthub from './kindtag-images/tool-dlthub-color.svg';
import docker from './kindtag-images/tool-docker-color.svg';
import duckdb from './kindtag-images/tool-duckdb-color.svg';
import excel from './kindtag-images/tool-excel-color.svg';
import facebook from './kindtag-images/tool-facebook-color.svg';
import fivetran from './kindtag-images/tool-fivetran-color.svg';
import gemini from './kindtag-images/tool-gemini-color.svg';
import github from './kindtag-images/tool-github-color.svg';
import gitlab from './kindtag-images/tool-gitlab-color.svg';
import go from './kindtag-images/tool-go-color.svg';
import google from './kindtag-images/tool-google-color.svg';
import googlecloud from './kindtag-images/tool-googlecloud-color.svg';
import googlesheets from './kindtag-images/tool-googlesheets-color.svg';
import graphql from './kindtag-images/tool-graphql-color.svg';
import greatexpectations from './kindtag-images/tool-greatexpectations-color.svg';
import hackernews from './kindtag-images/tool-hackernews-color.svg';
import hashicorp from './kindtag-images/tool-hashicorp-color.svg';
import hex from './kindtag-images/tool-hex-color.svg';
import hightouch from './kindtag-images/tool-hightouch-color.svg';
import hudi from './kindtag-images/tool-hudi-color.svg';
import huggingface from './kindtag-images/tool-huggingface-color.svg';
import iceberg from './kindtag-images/tool-iceberg-color.svg';
import instagram from './kindtag-images/tool-instagram-color.svg';
import java from './kindtag-images/tool-java-color.svg';
import javascript from './kindtag-images/tool-javascript-color.svg';
import jupyter from './kindtag-images/tool-jupyter-color.svg';
import k8s from './kindtag-images/tool-k8s-color.svg';
import lakefs from './kindtag-images/tool-lakefs-color.svg';
import lightgbm from './kindtag-images/tool-lightgbm-color.svg';
import linear from './kindtag-images/tool-linear-color.svg';
import linkedin from './kindtag-images/tool-linkedin-color.svg';
import llama from './kindtag-images/tool-llama-color.svg';
import looker from './kindtag-images/tool-looker-color.svg';
import matplotlib from './kindtag-images/tool-matplotlib-color.svg';
import meltano from './kindtag-images/tool-meltano-color.svg';
import meta from './kindtag-images/tool-meta-color.svg';
import metabase from './kindtag-images/tool-metabase-color.svg';
import microsoft from './kindtag-images/tool-microsoft-color.svg';
import minstral from './kindtag-images/tool-minstral-color.svg';
import mlflow from './kindtag-images/tool-mlflow-color.svg';
import modal from './kindtag-images/tool-modal-color.svg';
import mongodb from './kindtag-images/tool-mongodb-color.svg';
import montecarlo from './kindtag-images/tool-montecarlo-color.svg';
import mysql from './kindtag-images/tool-mysql-color.svg';
import noteable from './kindtag-images/tool-noteable-color.svg';
import notion from './kindtag-images/tool-notion-color.svg';
import numpy from './kindtag-images/tool-numpy-color.svg';
import omni from './kindtag-images/tool-omni-color.svg';
import openai from './kindtag-images/tool-openai-color.svg';
import openmetadata from './kindtag-images/tool-openmetadata-color.svg';
import optuna from './kindtag-images/tool-optuna-color.svg';
import oracle from './kindtag-images/tool-oracle-color.svg';
import pagerduty from './kindtag-images/tool-pagerduty-color.svg';
import pandas from './kindtag-images/tool-pandas-color.svg';
import pandera from './kindtag-images/tool-pandera-color.svg';
import papermill from './kindtag-images/tool-papermill-color.svg';
import papertrail from './kindtag-images/tool-papertrail-color.svg';
import parquet from './kindtag-images/tool-parquet-color.svg';
import plotly from './kindtag-images/tool-plotly-color.svg';
import plural from './kindtag-images/tool-plural-color.svg';
import polars from './kindtag-images/tool-polars-color.svg';
import postgres from './kindtag-images/tool-postgres-color.svg';
import powerbi from './kindtag-images/tool-powerbi-color.svg';
import prefect from './kindtag-images/tool-prefect-color.svg';
import python from './kindtag-images/tool-python-color.svg';
import pytorch from './kindtag-images/tool-pytorch-color.svg';
import pytorchlightning from './kindtag-images/tool-pytorchlightning-color.svg';
import r from './kindtag-images/tool-r-color.svg';
import ray from './kindtag-images/tool-ray-color.svg';
import react from './kindtag-images/tool-react-color.svg';
import reddit from './kindtag-images/tool-reddit-color.svg';
import redshift from './kindtag-images/tool-redshift-color.svg';
import rockset from './kindtag-images/tool-rockset-color.svg';
import rust from './kindtag-images/tool-rust-color.svg';
import s3 from './kindtag-images/tool-s3-color.svg';
import sagemaker from './kindtag-images/tool-sagemaker-color.svg';
import salesforce from './kindtag-images/tool-salesforce-color.svg';
import scala from './kindtag-images/tool-scala-color.svg';
import scikitlearn from './kindtag-images/tool-scikitlearn-color.svg';
import scipy from './kindtag-images/tool-scipy-color.svg';
import sdf from './kindtag-images/tool-sdf-color.svg';
import secoda from './kindtag-images/tool-secoda-color.svg';
import segment from './kindtag-images/tool-segment-color.svg';
import sharepoint from './kindtag-images/tool-sharepoint-color.svg';
import shell from './kindtag-images/tool-shell-color.svg';
import shopify from './kindtag-images/tool-shopify-color.svg';
import slack from './kindtag-images/tool-slack-color.svg';
import sling from './kindtag-images/tool-sling-color.svg';
import snowflake from './kindtag-images/tool-snowflake-color.svg';
import soda from './kindtag-images/tool-soda-color.svg';
import spark from './kindtag-images/tool-spark-color.svg';
import sql from './kindtag-images/tool-sql-color.svg';
import sqlite from './kindtag-images/tool-sqlite-color.svg';
import sqlmesh from './kindtag-images/tool-sqlmesh-color.svg';
import sqlserver from './kindtag-images/tool-sqlserver-color.svg';
import stepfuncitons from './kindtag-images/tool-stepfunctions-color.svg';
import stitch from './kindtag-images/tool-stitch-color.svg';
import stripe from './kindtag-images/tool-stripe-color.svg';
import tableau from './kindtag-images/tool-tableau-color.svg';
import teams from './kindtag-images/tool-teams-color.svg';
import tecton from './kindtag-images/tool-tecton-color.svg';
import tensorflow from './kindtag-images/tool-tensorflow-color.svg';
import thoughtspot from './kindtag-images/tool-thoughtspot-color.svg';
import trino from './kindtag-images/tool-trino-color.svg';
import twilio from './kindtag-images/tool-twilio-color.svg';
import typescript from './kindtag-images/tool-typescript-color.svg';
import vercel from './kindtag-images/tool-vercel-color.svg';
import wandb from './kindtag-images/tool-w&b-color.svg';
import x from './kindtag-images/tool-x-color.svg';
import xgboost from './kindtag-images/tool-xgboost-color.svg';
import youtube from './kindtag-images/tool-youtube-color.svg';
import view from './kindtag-images/view.svg';
import yaml from './kindtag-images/yaml.svg';

export interface IOpTag {
  label: string;
  onClick: (e: React.MouseEvent) => void;
}

interface OpTagsProps {
  style: React.CSSProperties;
  tags: IOpTag[];
  reduceColor?: boolean;
  reduceText?: boolean;
  reversed?: boolean;
}

type KnownTag = {
  color?: string | null;
  icon?: StaticImageData | string;
  content: string;
  blackAndWhite?: boolean;
};

export type KnownTagType =
  | 'jupyter'
  | 'ipynb'
  | 'noteable'
  | 'airbyte'
  | 'sling'
  | 'snowflake'
  | 'snowpark'
  | 'python'
  | 'fivetran'
  | 'dbt'
  | 'slack'
  | 'pytorch'
  | 'pyspark'
  | 'spark'
  | 'duckdb'
  | 'tensorflow'
  | 'pandas'
  | 'googlesheets'
  | 'sql'
  | 'wandb'
  | 'databricks'
  | 'airflow'
  | 'airtable'
  | 'omni'
  | 'datadog'
  | 'postgres'
  | 'postgresql'
  | 'stripe'
  | 'sigma'
  | 'hightouch'
  | 'census'
  | 'hex'
  | 'azure'
  | 'azureml'
  | 'sagemaker'
  | 'bigquery'
  | 'teams'
  | 'mlflow'
  | 'mysql'
  | 'greatexpectations'
  | 'powerbi'
  | 'gcp'
  | 'googlecloud'
  | 'looker'
  | 'tableau'
  | 'segment'
  | 'athena'
  | 's3'
  | 'aws'
  | 'stitch'
  | 'openai'
  | 'vercel'
  | 'github'
  | 'gitlab'
  | 'plotly'
  | 'modal'
  | 'meltano'
  | 'matplotlib'
  | 'numpy'
  | 'scipy'
  | 'scikitlearn'
  | 'kubernetes'
  | 'k8s'
  | 'polars'
  | 'catboost'
  | 'rust'
  | 'pytorchlightning'
  | 'deltalake'
  | 'parquet'
  | 'lightgbm'
  | 'xgboost'
  | 'rockset'
  | 'optuna'
  | 'chalk'
  | 'excel'
  | 'ray'
  | 'axioma'
  | 'cube'
  | 'metabase'
  | 'linear'
  | 'notion'
  | 'hackernewsapi'
  | 'hackernews'
  | 'tecton'
  | 'dask'
  | 'dlt'
  | 'dlthub'
  | 'huggingface'
  | 'huggingfaceapi'
  | 'sqlserver'
  | 'mongodb'
  | 'atlan'
  | 'celery'
  | 'claude'
  | 'collibra'
  | 'datahub'
  | 'discord'
  | 'docker'
  | 'facebook'
  | 'gemini'
  | 'google'
  | 'graphql'
  | 'hashicorp'
  | 'hudi'
  | 'iceberg'
  | 'instagram'
  | 'lakefs'
  | 'linkedin'
  | 'llama'
  | 'meta'
  | 'microsoft'
  | 'minstral'
  | 'montecarlo'
  | 'openmetadata'
  | 'oracle'
  | 'pagerduty'
  | 'pandera'
  | 'papermill'
  | 'papertrail'
  | 'plural'
  | 'prefect'
  | 'react'
  | 'reddit'
  | 'redshift'
  | 'salesforce'
  | 'sdf'
  | 'secoda'
  | 'shell'
  | 'shopify'
  | 'soda'
  | 'sqlite'
  | 'sqlmesh'
  | 'stepfuncitons'
  | 'awsstepfuncitons'
  | 'awssetepfunciton'
  | 'setepfunciton'
  | 'thoughtspot'
  | 'trino'
  | 'twilio'
  | 'twitter'
  | 'x'
  | 'youtube'
  | 'typescript'
  | 'javascript'
  | 'scala'
  | 'csharp'
  | 'cplus'
  | 'cplusplus'
  | 'java'
  | 'go'
  | 'r'
  | 'net'
  | 'sharepoint'
  | 'table'
  | 'view'
  | 'dag'
  | 'task'
  | 'source'
  | 'seed'
  | 'file'
  | 'dashboard'
  | 'notebook'
  | 'csv'
  | 'pdf'
  | 'yaml'
  | 'gold'
  | 'silver'
  | 'bronze'
  | 'expand';

export const KNOWN_TAGS: Record<KnownTagType, KnownTag> = {
  jupyter: {
    icon: jupyter,
    content: 'jupyter',
  },
  ipynb: {
    icon: jupyter,
    content: 'ipynb',
  },
  noteable: {
    icon: noteable,
    content: 'Noteable',
  },
  airbyte: {
    icon: airbyte,
    content: 'Airbyte',
  },
  sling: {
    icon: sling,
    content: 'Sling',
  },
  snowflake: {
    icon: snowflake,
    content: 'Snowflake',
  },
  snowpark: {
    icon: snowflake,
    content: 'Snowpark',
  },
  python: {
    icon: python,
    content: 'Python',
  },
  fivetran: {
    icon: fivetran,
    content: 'Fivetran',
  },
  dbt: {
    icon: dbt,
    content: 'dbt',
  },
  slack: {
    icon: slack,
    content: 'Slack',
  },
  pytorch: {
    icon: pytorch,
    content: 'PyTorch',
  },
  pyspark: {
    icon: spark,
    content: 'PySpark',
  },
  spark: {
    icon: spark,
    content: 'Spark',
  },
  duckdb: {
    icon: duckdb,
    content: 'DuckDB',
  },
  tensorflow: {
    icon: tensorflow,
    content: 'TensorFlow',
  },
  pandas: {
    icon: pandas,
    content: 'pandas',
  },
  googlesheets: {
    icon: googlesheets,
    content: 'Google Sheets',
  },
  sql: {
    icon: sql,
    content: 'SQL',
  },
  wandb: {
    icon: wandb,
    content: 'Weights & Biases',
  },
  databricks: {
    icon: databricks,
    content: 'Databricks',
  },
  airflow: {
    icon: airflow,
    content: 'Airflow',
  },
  airtable: {
    icon: airtable,
    content: 'Airtable',
  },
  omni: {
    icon: omni,
    content: 'Omni',
  },
  datadog: {
    icon: datadog,
    content: 'Datadog',
  },
  postgres: {
    icon: postgres,
    content: 'Postgres',
  },
  postgresql: {
    icon: postgres,
    content: 'PostgreSQL',
  },
  stripe: {
    icon: stripe,
    content: 'Stripe',
  },
  sigma: {
    icon: sigma,
    content: 'Sigma',
    blackAndWhite: true,
  },
  hightouch: {
    icon: hightouch,
    content: 'Hightouch',
  },
  census: {
    icon: census,
    content: 'Census',
  },
  hex: {
    icon: hex,
    content: 'Hex',
    blackAndWhite: true,
  },
  azure: {
    icon: azure,
    content: 'Azure',
  },
  azureml: {
    icon: azureml,
    content: 'Azure ML',
  },
  sagemaker: {
    icon: sagemaker,
    content: 'Sagemaker',
  },
  bigquery: {
    icon: bigquery,
    content: 'BigQuery',
  },
  teams: {
    icon: teams,
    content: 'Teams',
  },
  mlflow: {
    icon: mlflow,
    content: 'ML Flow',
  },
  mysql: {
    icon: mysql,
    content: 'MySQL',
  },
  greatexpectations: {
    icon: greatexpectations,
    content: 'Great Expectations',
  },
  powerbi: {
    icon: powerbi,
    content: 'Power BI',
  },
  gcp: {
    icon: googlecloud,
    content: 'GCP',
  },
  googlecloud: {
    icon: googlecloud,
    content: 'Google Cloud',
  },
  looker: {
    icon: looker,
    content: 'Looker',
  },
  tableau: {
    icon: tableau,
    content: 'Tableau',
  },
  segment: {
    icon: segment,
    content: 'Segment',
  },
  athena: {
    icon: aws,
    content: 'Athena',
  },
  s3: {
    icon: s3,
    content: 'S3',
  },
  aws: {
    icon: aws,
    content: 'AWS',
  },
  stitch: {
    icon: stitch,
    content: 'Stitch',
  },
  openai: {
    icon: openai,
    content: 'Open AI',
  },
  vercel: {
    icon: vercel,
    content: 'Vercel',
    blackAndWhite: true,
  },
  github: {
    icon: github,
    content: 'Github',
    blackAndWhite: true,
  },
  gitlab: {
    icon: gitlab,
    content: 'Gitlab',
  },
  plotly: {
    icon: plotly,
    content: 'plotly',
  },
  modal: {
    icon: modal,
    content: 'Modal',
  },
  meltano: {
    icon: meltano,
    content: 'Meltano',
  },
  matplotlib: {
    icon: matplotlib,
    content: 'matplotlib',
  },
  numpy: {
    icon: numpy,
    content: 'NumPy',
  },
  scipy: {
    icon: scipy,
    content: 'SciPy',
  },
  scikitlearn: {
    icon: scikitlearn,
    content: 'Scikit Learn',
  },
  kubernetes: {
    icon: k8s,
    content: 'Kubernetes',
  },
  k8s: {
    icon: k8s,
    content: 'K8s',
  },
  polars: {
    icon: polars,
    content: 'Polars',
    blackAndWhite: true,
  },
  catboost: {
    icon: catboost,
    content: 'CatBoost',
  },
  rust: {
    icon: rust,
    content: 'Rust',
    blackAndWhite: true,
  },
  pytorchlightning: {
    icon: pytorchlightning,
    content: 'Pytorch Lightning',
  },
  deltalake: {
    icon: delta_lake,
    content: 'Delta Lake',
  },
  parquet: {
    icon: parquet,
    content: 'Parquet',
  },
  lightgbm: {
    icon: lightgbm,
    content: 'lightgbm',
  },
  xgboost: {
    icon: xgboost,
    content: 'XGBoost',
  },
  rockset: {
    icon: rockset,
    content: 'Rockset',
  },
  optuna: {
    icon: optuna,
    content: 'Optuna',
  },
  chalk: {
    icon: chalk,
    content: 'Chalk',
    blackAndWhite: true,
  },
  excel: {
    icon: excel,
    content: 'Excel',
  },
  ray: {
    icon: ray,
    content: 'Ray',
    blackAndWhite: true,
  },
  axioma: {
    icon: axioma,
    content: 'Axioma',
  },
  cube: {
    icon: cube,
    content: 'Cube',
  },
  metabase: {
    icon: metabase,
    content: 'Metabase',
  },
  linear: {
    icon: linear,
    content: 'Linear',
  },
  notion: {
    icon: notion,
    content: 'Notion',
    blackAndWhite: true,
  },
  hackernewsapi: {
    icon: hackernews,
    content: 'Hacker News',
  },
  hackernews: {
    icon: hackernews,
    content: 'Hacker News API',
  },
  tecton: {
    icon: tecton,
    content: 'Tecton',
  },
  dask: {
    icon: dask,
    content: 'Dask',
  },
  dlt: {
    icon: dlthub,
    content: 'dlt',
  },
  dlthub: {
    icon: dlthub,
    content: 'dlthub',
  },
  huggingface: {
    icon: huggingface,
    content: 'Hugging Face',
  },
  huggingfaceapi: {
    icon: huggingface,
    content: 'Hugging Face',
  },
  sqlserver: {
    icon: sqlserver,
    content: 'Microsoft SQL Server',
  },
  mongodb: {
    icon: mongodb,
    content: 'MongoDB',
  },
  atlan: {
    icon: atlan,
    content: 'Atlan',
  },
  celery: {
    icon: celery,
    content: 'Celery',
  },
  claude: {
    icon: claude,
    content: 'Claude',
  },
  collibra: {
    icon: collibra,
    content: 'Collibra',
  },
  datahub: {
    icon: datahub,
    content: 'Datahub',
  },
  discord: {
    icon: discord,
    content: 'Discord',
  },
  docker: {
    icon: docker,
    content: 'Docker',
  },
  facebook: {
    icon: facebook,
    content: 'Facebook',
  },
  gemini: {
    icon: gemini,
    content: 'Gemini',
  },
  google: {
    icon: google,
    content: 'Google',
  },
  graphql: {
    icon: graphql,
    content: 'GraphQL',
  },
  hashicorp: {
    icon: hashicorp,
    content: 'Hashicorp',
  },
  hudi: {
    icon: hudi,
    content: 'Hudi',
  },
  iceberg: {
    icon: iceberg,
    content: 'Iceberg',
  },
  instagram: {
    icon: instagram,
    content: 'Instagram',
  },
  lakefs: {
    icon: lakefs,
    content: 'LakeFS',
  },
  linkedin: {
    icon: linkedin,
    content: 'LinkedIn',
  },
  llama: {
    icon: llama,
    content: 'Llama',
  },
  meta: {
    icon: meta,
    content: 'Meta',
  },
  microsoft: {
    icon: microsoft,
    content: 'Microsoft',
  },
  minstral: {
    icon: minstral,
    content: 'Minstral',
  },
  montecarlo: {
    icon: montecarlo,
    content: 'Monte Carlo',
  },
  openmetadata: {
    icon: openmetadata,
    content: 'Open Metadata',
  },
  oracle: {
    icon: oracle,
    content: 'Oracle',
  },
  pagerduty: {
    icon: pagerduty,
    content: 'PagerDuty',
  },
  pandera: {
    icon: pandera,
    content: 'Pandera',
  },
  papermill: {
    icon: papermill,
    content: 'Papermill',
  },
  papertrail: {
    icon: papertrail,
    content: 'Papertrail',
  },
  plural: {
    icon: plural,
    content: 'Plural',
    blackAndWhite: true,
  },
  prefect: {
    icon: prefect,
    content: 'Prefect',
  },
  react: {
    icon: react,
    content: 'React',
  },
  reddit: {
    icon: reddit,
    content: 'Reddit',
  },
  redshift: {
    icon: redshift,
    content: 'Redshift',
  },
  salesforce: {
    icon: salesforce,
    content: 'Salesforce',
  },
  sdf: {
    icon: sdf,
    content: 'SDF',
  },
  secoda: {
    icon: secoda,
    content: 'Secoda',
  },
  shell: {
    icon: shell,
    content: 'Shell',
    blackAndWhite: true,
  },
  shopify: {
    icon: shopify,
    content: 'Shopify',
  },
  soda: {
    icon: soda,
    content: 'Soda',
  },
  sqlite: {
    icon: sqlite,
    content: 'SQLite',
  },
  sqlmesh: {
    icon: sqlmesh,
    content: 'SQLMesh',
  },
  stepfuncitons: {
    icon: stepfuncitons,
    content: 'Step Functions',
  },
  awsstepfuncitons: {
    icon: stepfuncitons,
    content: 'Step Functions',
  },
  awssetepfunciton: {
    icon: stepfuncitons,
    content: 'Step Functions',
  },
  setepfunciton: {
    icon: stepfuncitons,
    content: 'Step Functions',
  },
  thoughtspot: {
    icon: thoughtspot,
    content: 'Thoughtspot',
    blackAndWhite: true,
  },
  trino: {
    icon: trino,
    content: 'Trino',
  },
  twilio: {
    icon: twilio,
    content: 'Twilio',
  },
  twitter: {
    icon: x,
    content: 'Twitter',
    blackAndWhite: true,
  },
  x: {
    icon: x,
    content: ' ',
    blackAndWhite: true,
  },
  youtube: {
    icon: youtube,
    content: 'YouTube',
  },
  typescript: {
    icon: typescript,
    content: 'TypeScript',
  },
  javascript: {
    icon: javascript,
    content: 'JavaScript',
  },
  scala: {
    icon: scala,
    content: 'Scala',
  },
  csharp: {
    icon: csharp,
    content: 'C#',
  },
  cplus: {
    icon: cplus,
    content: 'C++',
  },
  cplusplus: {
    icon: cplus,
    content: 'C++',
  },
  java: {
    icon: java,
    content: 'Java',
  },
  go: {
    icon: go,
    content: 'Go',
  },
  r: {
    icon: r,
    content: ' ',
  },
  net: {
    icon: microsoft,
    content: '.net',
  },
  sharepoint: {
    icon: sharepoint,
    content: 'Sharepoint',
  },
  table: {
    icon: table,
    content: 'Table',
    blackAndWhite: true,
  },
  view: {
    icon: view,
    content: 'View',
    blackAndWhite: true,
  },
  dag: {
    icon: dag,
    content: 'Dag',
    blackAndWhite: true,
  },
  task: {
    icon: task,
    content: 'Task',
    blackAndWhite: true,
  },
  source: {
    icon: source,
    content: 'Source',
    blackAndWhite: true,
  },
  seed: {
    icon: seed,
    content: 'Seed',
    blackAndWhite: true,
  },
  file: {
    icon: file,
    content: 'File',
    blackAndWhite: true,
  },
  dashboard: {
    icon: dashboard,
    content: 'Dashboard',
    blackAndWhite: true,
  },
  notebook: {
    icon: notebook,
    content: 'Notebook',
    blackAndWhite: true,
  },
  csv: {
    icon: csv,
    content: ' ',
    blackAndWhite: true,
  },
  pdf: {
    icon: pdf,
    content: ' ',
    blackAndWhite: true,
  },
  yaml: {
    icon: yaml,
    content: ' ',
    blackAndWhite: true,
  },
  gold: {
    icon: medallion_gold,
    content: 'Gold',
  },
  silver: {
    icon: medallion_silver,
    content: 'Silver',
  },
  bronze: {
    icon: medallion_bronze,
    content: 'Bronze',
  },
  expand: {color: '#D7A540', content: 'Expand'},
};

// google-sheets to googlesheets, Duckdb to duckdb
function coerceToStandardLabel(label: string) {
  return label.replace(/[ _.-]/g, '').toLowerCase();
}

export const extractIconSrc = (knownTag: KnownTag | undefined) => {
  // Storybook imports SVGs are string but nextjs imports them as object.
  // This is a temporary work around until we can get storybook to import them the same way as nextjs
  if (typeof knownTag?.icon !== 'undefined') {
    return typeof knownTag.icon === 'string' ? (knownTag.icon as any) : knownTag.icon?.src;
  }
  return '';
};

export const OpTags = React.memo(({tags, style, reduceColor, reduceText}: OpTagsProps) => {
  return (
    <OpTagsContainer style={style}>
      {tags.map((tag) => {
        const known = KNOWN_TAGS[coerceToStandardLabel(tag.label) as KnownTagType];
        const blackAndWhite = known && 'blackAndWhite' in known && known.blackAndWhite;
        const text = known?.content || tag.label;

        return (
          <Box
            key={tag.label}
            flex={{gap: 4, alignItems: 'center'}}
            data-tooltip={reduceText ? text : undefined}
            onClick={tag.onClick}
            style={{
              background: reduceColor ? Colors.backgroundGray() : Colors.lineageNodeBackground(),
              fontWeight: reduceColor ? 500 : 600,
            }}
          >
            {known && 'icon' in known && (
              <OpTagIconWrapper
                role="img"
                $size={16}
                $img={extractIconSrc(known)}
                $color={blackAndWhite ? Colors.accentPrimary() : null}
                $rotation={null}
                aria-label={tag.label}
              />
            )}
            {known && 'icon' in known && reduceText ? undefined : text}
          </Box>
        );
      })}
    </OpTagsContainer>
  );
});

export const TagIcon = React.memo(({label}: {label: string}) => {
  const known = KNOWN_TAGS[coerceToStandardLabel(label) as KnownTagType];
  const blackAndWhite = known && 'blackAndWhite' in known && known.blackAndWhite;
  if (known && 'icon' in known) {
    return (
      <OpTagIconWrapper
        role="img"
        $size={16}
        $img={extractIconSrc(known)}
        $color={blackAndWhite ? Colors.accentPrimary() : null}
        $rotation={null}
        aria-label={label}
      />
    );
  }
  return null;
});

const OpTagIconWrapper = styled(IconWrapper)`
  mask-size: contain;
  mask-repeat: no-repeat;
  mask-position: center;
  -webkit-mask-size: contain;
  -webkit-mask-repeat: no-repeat;
  -webkit-mask-position: center;
`;

const OpTagsContainer = styled.div`
  gap: 6px;
  position: absolute;
  display: flex;
  margin-right: 14px;

  & > div {
    padding: 0 8px;
    min-height: 24px;
    display: flex;
    align-items: center;
    font-family: ${FontFamily.default};
    font-size: 12px;
    border-radius: 8px;
  }
`;
