import {Box, FontFamily, IconWrapper, Colors} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import airbyte from './optag-images/airbyte.svg';
import airflow from './optag-images/airflow.svg';
import airtable from './optag-images/airtable.svg';
import aws from './optag-images/aws.svg';
import axioma from './optag-images/axioma.svg';
import azure from './optag-images/azure.svg';
import azureml from './optag-images/azureml.svg';
import bigquery from './optag-images/bigquery.svg';
import catboost from './optag-images/catboost.svg';
import census from './optag-images/census.svg';
import chalk from './optag-images/chalk.svg';
import cube from './optag-images/cube.svg';
import dask from './optag-images/dask.svg';
import databricks from './optag-images/databricks.svg';
import datadog from './optag-images/datadog.svg';
import dbt from './optag-images/dbt.svg';
import delta_lake from './optag-images/delta_lake.svg';
import dlthub from './optag-images/dlthub.svg';
import duckdb from './optag-images/duckdb.svg';
import excel from './optag-images/excel.svg';
import fivetran from './optag-images/fivetran.svg';
import github from './optag-images/github.svg';
import gitlab from './optag-images/gitlab.svg';
import googlecloud from './optag-images/googlecloud.svg';
import googlesheets from './optag-images/googlesheets.svg';
import great_expectations from './optag-images/great_expectations.svg';
import hackernewsapi from './optag-images/hackernewsapi.svg';
import hex from './optag-images/hex.svg';
import hightouch from './optag-images/hightouch.svg';
import huggingface from './optag-images/huggingface.svg';
import jax from './optag-images/jax.svg';
import jupyter from './optag-images/jupyter.svg';
import k8s from './optag-images/k8s.svg';
import keras from './optag-images/keras.svg';
import lightgbm from './optag-images/lightgbm.svg';
import linear from './optag-images/linear.svg';
import looker from './optag-images/looker.svg';
import matplotlib from './optag-images/matplotlib.svg';
import meltano from './optag-images/meltano.svg';
import metabase from './optag-images/metabase.svg';
import mlflow from './optag-images/mlflow.svg';
import modal from './optag-images/modal.svg';
import teams from './optag-images/msteams.svg';
import noteable from './optag-images/noteable.svg';
import notion from './optag-images/notion.svg';
import numpy from './optag-images/numpy.svg';
import omni from './optag-images/omni.svg';
import openai from './optag-images/openai.svg';
import optuna from './optag-images/optuna.svg';
import pandas from './optag-images/pandas.svg';
import parquet from './optag-images/parquet.svg';
import plotly from './optag-images/plotly.svg';
import polars from './optag-images/polars.svg';
import postgres from './optag-images/postgres.svg';
import powerbi from './optag-images/powerbi.svg';
import pyspark from './optag-images/pyspark.svg';
import python from './optag-images/python.svg';
import pytorch from './optag-images/pytorch.svg';
import pytorch_lightning from './optag-images/pytorch_lightning.svg';
import ray from './optag-images/ray.svg';
import rockset from './optag-images/rockset.svg';
import rust from './optag-images/rust.svg';
import sagemaker from './optag-images/sagemaker.svg';
import scikitlearn from './optag-images/scikitlearn.svg';
import scipy from './optag-images/scipy.svg';
import segment from './optag-images/segment.svg';
import slack from './optag-images/slack.svg';
import sling from './optag-images/sling.svg';
import snowflake from './optag-images/snowflake.svg';
import sql from './optag-images/sql.svg';
import stitch from './optag-images/stitch.svg';
import stripe from './optag-images/stripe.svg';
import tableau from './optag-images/tableau.svg';
import tecton from './optag-images/tecton.svg';
import tensorflow from './optag-images/tensorflow.svg';
import vercel from './optag-images/vercel.svg';
import weights_and_biases from './optag-images/weights_and_biases.svg';
import xgboost from './optag-images/xgboost.svg';

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

export const KNOWN_TAGS = {
  jupyter: {
    color: '#929292',
    icon: jupyter,
    content: 'Jupyter',
  },
  ipynb: {
    color: '#4E4E4E',
    icon: jupyter,
    content: 'Jupyter',
    reversed: true,
  },
  noteable: {
    color: '#00D2D2',
    icon: noteable,
    content: 'Noteable',
  },
  airbyte: {
    color: '#655CFC',
    icon: airbyte,
    content: 'Airbyte',
  },
  sling: {
    color: '#2176EA',
    icon: sling,
    content: 'Sling',
  },
  snowflake: {
    color: '#29B5E8',
    icon: snowflake,
    content: 'Snowflake',
  },
  snowpark: {
    color: '#29B5E8',
    icon: snowflake,
    content: 'Snowpark',
  },
  python: {
    color: '#367EF0',
    icon: python,
    content: 'Python',
  },
  fivetran: {
    color: '#0073FF',
    icon: fivetran,
    content: 'Fivetran',
  },
  dbt: {
    color: '#FF6B4C',
    icon: dbt,
    content: 'dbt',
  },
  slack: {
    color: null,
    icon: slack,
    content: 'Slack',
  },
  pytorch: {
    color: '#EE4C2C',
    icon: pytorch,
    content: 'PyTorch',
  },
  pyspark: {
    color: '#C74D15',
    icon: pyspark,
    content: 'PySpark',
  },
  spark: {
    color: '#C74D15',
    icon: pyspark,
    content: 'Spark',
  },
  duckdb: {
    color: '#FCBC41',
    icon: duckdb,
    content: 'DuckDB',
  },
  tensorflow: {
    color: '#FE9413',
    icon: tensorflow,
    content: 'TensorFlow',
  },
  pandas: {
    color: '#E40385',
    icon: pandas,
    content: 'pandas',
    reversed: true,
  },
  googlesheets: {
    color: '#23A566',
    icon: googlesheets,
    content: 'Google Sheets',
  },
  sql: {
    color: '#B821FF',
    icon: sql,
    content: 'SQL',
  },
  wandb: {
    color: '#FFBE00',
    icon: weights_and_biases,
    content: 'Weights & Biases',
  },
  databricks: {
    color: '#FD3820',
    icon: databricks,
    content: 'Databricks',
  },
  airflow: {
    color: null,
    icon: airflow,
    content: 'Airflow',
  },
  airtable: {
    color: null,
    icon: airtable,
    content: 'Airtable',
  },
  omni: {
    color: null,
    icon: omni,
    content: 'Omni',
  },
  datadog: {
    color: '#7633C8',
    icon: datadog,
    content: 'Datadog',
    reversed: true,
  },
  postgres: {
    color: '#136FBA',
    icon: postgres,
    content: 'Postgres',
  },
  stripe: {
    color: '#635BFF',
    icon: stripe,
    content: 'Stripe',
  },
  hightouch: {
    color: '#4EBB6C',
    icon: hightouch,
    content: 'Hightouch',
  },
  census: {
    color: '#EF54AC',
    icon: census,
    content: 'Census',
  },
  hex: {
    color: '#473982',
    icon: hex,
    content: 'Hex',
    reversed: true,
  },
  azure: {
    color: '#39C3F1',
    icon: azure,
    content: 'Azure',
  },
  azureml: {
    color: '#39C3F1',
    icon: azureml,
    content: 'Azure ML',
  },
  sagemaker: {
    color: '#A164FD',
    icon: sagemaker,
    content: 'Sagemaker',
  },
  bigquery: {
    color: '#4485F4',
    icon: bigquery,
    content: 'BigQuery',
  },
  teams: {
    color: '#5255A9',
    icon: teams,
    content: 'Teams',
  },
  mlflow: {
    color: '#0194E2',
    icon: mlflow,
    content: 'ML Flow',
  },
  greatexpectations: {
    color: '#FF6310',
    icon: great_expectations,
    content: 'Great Expectations',
  },
  powerbi: {
    color: '#EDC947',
    icon: powerbi,
    content: 'Power BI',
  },
  gcp: {
    color: '#4285F4',
    icon: googlecloud,
    content: 'GCP',
  },
  googlecloud: {
    color: '#4285F4',
    icon: googlecloud,
    content: 'Google Cloud',
  },
  looker: {
    color: '#929292',
    icon: looker,
    content: 'Looker',
  },
  tableau: {
    color: '#2E5EB1',
    icon: tableau,
    content: 'Tableau',
  },
  segment: {
    color: '#43AF79',
    icon: segment,
    content: 'Segment',
  },
  athena: {
    color: '#FF9900',
    icon: aws,
    content: 'Athena',
  },
  s3: {
    color: '#FF9900',
    icon: aws,
    content: 'S3',
  },
  aws: {
    color: '#FF9900',
    icon: aws,
    content: 'AWS',
  },
  stitch: {
    color: '#FFD201',
    icon: stitch,
    content: 'Stitch',
  },
  openai: {
    color: '#4AA081',
    icon: openai,
    content: 'Open AI',
  },
  vercel: {
    color: '#787878',
    icon: vercel,
    content: 'Vercel',
    reversed: true,
  },
  github: {
    color: '#A970C1',
    icon: github,
    content: 'Github',
    reversed: true,
  },
  gitlab: {
    color: '#E24329',
    icon: gitlab,
    content: 'Gitlab',
  },
  plotly: {
    color: '#787AF7',
    icon: plotly,
    content: 'plotly',
  },
  modal: {
    color: '#4CDE29',
    icon: modal,
    content: 'Modal',
    reversed: true,
  },
  meltano: {
    color: '#3537BE',
    icon: meltano,
    content: 'Meltano',
    reversed: true,
  },
  matplotlib: {
    color: '#055998',
    icon: matplotlib,
    content: 'matplotlib',
  },
  numpy: {
    color: '#4D77CF',
    icon: numpy,
    content: 'NumPy',
  },
  scipy: {
    color: '#0054A6',
    icon: scipy,
    content: 'SciPy',
  },
  scikitlearn: {
    color: '#F7931E',
    icon: scikitlearn,
    content: 'Scikit Learn',
  },
  keras: {
    color: '#D00000',
    icon: keras,
    content: 'Keras',
  },
  kubernetes: {
    color: '#326CE5',
    icon: k8s,
    content: 'Kubernetes',
  },
  k8s: {
    color: '#326CE5',
    icon: k8s,
    content: 'K8s',
  },
  polars: {
    color: '#24292E',
    icon: polars,
    content: 'Polars',
  },
  catboost: {
    color: null,
    icon: catboost,
    content: 'CatBoost',
  },
  rust: {
    color: '#000000',
    icon: rust,
    content: 'Rust',
    reversed: true,
  },
  pytorchlightning: {
    color: null,
    icon: pytorch_lightning,
    content: 'Pytorch Lightning',
  },
  deltalake: {
    color: '#00ADD4',
    icon: delta_lake,
    content: 'Delta Lake',
  },
  parquet: {
    color: '#50ABF1',
    icon: parquet,
    content: 'Parquet',
  },
  lightgbm: {
    color: null,
    icon: lightgbm,
    content: 'lightgbm',
  },
  xgboost: {
    color: '#1A9EDB',
    icon: xgboost,
    content: 'XGBoost',
  },
  jax: {
    color: null,
    icon: jax,
    content: 'JAX',
  },
  rockset: {
    color: null,
    icon: rockset,
    content: 'Rockset',
  },
  optuna: {
    color: '#1488C9',
    icon: optuna,
    content: 'Optuna',
  },
  chalk: {
    color: '#000000',
    icon: chalk,
    content: 'Chalk',
    reversed: true,
  },
  excel: {
    color: '#00A651',
    icon: excel,
    content: 'Excel',
  },
  ray: {
    color: '#00A2E9',
    icon: ray,
    content: 'Ray',
  },
  axioma: {
    color: '#0774B6',
    icon: axioma,
    content: 'Axioma',
  },
  cube: {
    color: null,
    icon: cube,
    content: 'Cube',
  },
  metabase: {
    color: '#509EE3',
    icon: metabase,
    content: 'Metabase',
  },
  linear: {
    color: '#5E6AD2',
    icon: linear,
    content: 'Linear',
  },
  notion: {
    color: '#000000',
    icon: notion,
    content: 'Notion',
    reversed: true,
  },
  hackernewsapi: {
    color: '#FB651E',
    icon: hackernewsapi,
    content: 'Hacker News API',
  },
  tecton: {
    color: '#D30602',
    icon: tecton,
    content: 'Tecton',
  },
  dask: {
    color: null,
    icon: dask,
    content: 'Dask',
  },
  dlt: {
    color: null,
    icon: dlthub,
    content: 'dlt',
  },
  dlthub: {
    color: null,
    icon: dlthub,
    content: 'dlthub',
  },
  huggingface: {
    color: null,
    icon: huggingface,
    content: 'Hugging Face',
  },
  huggingfaceapi: {
    color: null,
    icon: huggingface,
    content: 'Hugging Face',
  },
  expand: {color: '#D7A540', content: 'Expand'},
};

// google-sheets to googlesheets, Duckdb to duckdb
function coerceToStandardLabel(label: string) {
  return label.replace(/[ _-]/g, '').toLowerCase();
}

export const AssetComputeKindTag = ({
  definition,
  ...rest
}: {
  definition: {computeKind: string | null};
  style: React.CSSProperties;
  reduceColor?: boolean;
  reduceText?: boolean;
  reversed?: boolean;
}) => {
  if (!definition.computeKind) {
    return null;
  }
  return (
    <OpTags
      {...rest}
      tags={[
        {
          label: definition.computeKind,
          onClick: () => {
            window.requestAnimationFrame(() => document.dispatchEvent(new Event('show-kind-info')));
          },
        },
      ]}
    />
  );
};

export const OpTags = React.memo(({tags, style, reduceColor, reduceText}: OpTagsProps) => {
  return (
    <OpTagsContainer style={style}>
      {tags.map((tag) => {
        const known = KNOWN_TAGS[coerceToStandardLabel(tag.label) as keyof typeof KNOWN_TAGS];
        const text = known?.content || tag.label;
        // NULL color means we inherit the color from the svg.
        // This is useful when the icon requires mulltiple colors. like Airflow.
        const color = known?.color || null;
        const reversed = known && 'reversed' in known ? known.reversed : false;
        return (
          <Box
            key={tag.label}
            flex={{gap: 4, alignItems: 'center'}}
            data-tooltip={reduceText ? text : undefined}
            onClick={tag.onClick}
            style={{
              background: reduceColor ? Colors.backgroundGray() : Colors.lineageNodeBackground(),
              fontWeight: reduceColor ? 500 : 700,
            }}
          >
            {known && 'icon' in known && (
              <OpTagIconWrapper
                role="img"
                $size={16}
                $img={known.icon.src}
                $color={reversed ? Colors.accentPrimary() : color}
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
