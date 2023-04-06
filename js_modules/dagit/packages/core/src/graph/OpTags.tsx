import {Box, Colors, FontFamily, IconWrapper} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import airbyte from './optag-images/airbyte.svg';
import airflow from './optag-images/airflow.svg';
import aws from './optag-images/aws.svg';
import azure from './optag-images/azure.svg';
import azureml from './optag-images/azureml.svg';
import bigquery from './optag-images/bigquery.svg';
import census from './optag-images/census.svg';
import databricks from './optag-images/databricks.svg';
import datadog from './optag-images/datadog.svg';
import dbt from './optag-images/dbt.svg';
import duckdb from './optag-images/duckdb.svg';
import fivetran from './optag-images/fivetran.svg';
import github from './optag-images/github.svg';
import gitlab from './optag-images/gitlab.svg';
import googlecloud from './optag-images/googlecloud.svg';
import googlesheets from './optag-images/googlesheets.svg';
import great_expectations from './optag-images/great_expectations.svg';
import hex from './optag-images/hex.svg';
import hightouch from './optag-images/hightouch.svg';
import jupyter from './optag-images/jupyter.svg';
import k8s from './optag-images/k8s.svg';
import keras from './optag-images/keras.svg';
import looker from './optag-images/looker.svg';
import matplotlib from './optag-images/matplotlib.svg';
import meltano from './optag-images/meltano.svg';
import mlflow from './optag-images/mlflow.svg';
import modal from './optag-images/modal.svg';
import teams from './optag-images/msteams.svg';
import noteable from './optag-images/noteable.svg';
import numpy from './optag-images/numpy.svg';
import openai from './optag-images/openai.svg';
import pandas from './optag-images/pandas.svg';
import plotly from './optag-images/plotly.svg';
import postgres from './optag-images/postgres.svg';
import powerbi from './optag-images/powerbi.svg';
import pyspark from './optag-images/pyspark.svg';
import python from './optag-images/python.svg';
import pytorch from './optag-images/pytorch.svg';
import sagemaker from './optag-images/sagemaker.svg';
import scikitlearn from './optag-images/scikitlearn.svg';
import scipy from './optag-images/scipy.svg';
import segment from './optag-images/segment.svg';
import slack from './optag-images/slack.svg';
import snowflake from './optag-images/snowflake.svg';
import sql from './optag-images/sql.svg';
import stitch from './optag-images/stitch.svg';
import stripe from './optag-images/stripe.svg';
import tableau from './optag-images/tableau.svg';
import tensorflow from './optag-images/tensorflow.svg';
import vercel from './optag-images/vercel.svg';
import weights_and_biases from './optag-images/weights_and_biases.svg';

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
    color: '#4E4E4E',
    icon: jupyter,
    content: 'Jupyter',
  },
  ipynb: {
    color: '#4E4E4E',
    icon: jupyter,
    content: 'Jupyter',
  },
  noteable: {
    color: '#00D2D2',
    icon: noteable,
    content: 'Noteable',
    reversed: true,
  },
  airbyte: {
    color: '#655CFC',
    icon: airbyte,
    content: 'Airbyte',
  },
  snowflake: {
    color: '#29B5E8',
    icon: snowflake,
    content: 'Snowflake',
  },
  python: {
    color: '#35668F',
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
    color: '#4A144A',
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
    reversed: true,
  },
  tensorflow: {
    color: '#FE9413',
    icon: tensorflow,
    content: 'TensorFlow',
    reversed: true,
  },
  pandas: {
    color: '#130754',
    icon: pandas,
    content: 'pandas',
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
    color: '#FCB119',
    icon: weights_and_biases,
    content: 'Weights & Biases',
    reversed: true,
  },
  databricks: {
    color: '#FD3820',
    icon: databricks,
    content: 'Databricks',
  },
  airflow: {
    color: '#017CEE',
    icon: airflow,
    content: 'Airflow',
  },
  datadog: {
    color: '#632CA6',
    icon: datadog,
    content: 'Datadog',
  },
  postgres: {
    color: '#336791',
    icon: postgres,
    content: 'Postgres',
  },
  stripe: {
    color: '#635BFF',
    icon: stripe,
    content: 'Stripe',
  },
  hightouch: {
    color: '#07484D',
    icon: hightouch,
    content: 'Hightouch',
  },
  census: {
    color: '#EF54AC',
    icon: census,
    content: 'Census',
  },
  hex: {
    color: '#F5C0C0',
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
    reversed: true,
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
    color: '#5F6368',
    icon: looker,
    content: 'Looker',
  },
  tableau: {
    color: '#25447A',
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
    reversed: true,
  },
  s3: {
    color: '#FF9900',
    icon: aws,
    content: 'S3',
    reversed: true,
  },
  aws: {
    color: '#FF9900',
    icon: aws,
    content: 'AWS',
    reversed: true,
  },
  stitch: {
    color: '#FFD201',
    icon: stitch,
    content: 'Stitch',
    reversed: true,
  },
  openai: {
    color: '#4AA081',
    icon: openai,
    content: 'Open AI',
  },
  vercel: {
    color: '#171615',
    icon: vercel,
    content: 'Vercel',
  },
  github: {
    color: '#171615',
    icon: github,
    content: 'Github',
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
    color: '#9AEE86',
    icon: modal,
    content: 'Modal',
    reversed: true,
  },
  meltano: {
    color: '#311772',
    icon: meltano,
    content: 'Meltano',
  },
  matplotlib: {
    color: '#2B597C',
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
  expand: {color: '#D7A540', content: 'Expand'},
};

function generateColorForLabel(label = '') {
  return `hsl(${
    label
      .split('')
      .map((c) => c.charCodeAt(0))
      .reduce((n, a) => n + a) % 360
  }, 75%, 45%)`;
}

// google-sheets to googlesheets, Duckdb to duckdb
function coerceToStandardLabel(label: string) {
  return label.replace(/[ _-]/g, '').toLowerCase();
}

export const AssetComputeKindTag: React.FC<{
  definition: {computeKind: string | null};
  style: React.CSSProperties;
  reduceColor?: boolean;
  reduceText?: boolean;
  reversed?: boolean;
}> = ({definition, ...rest}) => {
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
        const known = (KNOWN_TAGS as any)[coerceToStandardLabel(tag.label)];
        const text = known?.content || tag.label;
        const color = known?.color || generateColorForLabel(tag.label);
        const textcolor = known?.reversed ? Colors.Gray900 : Colors.White;
        return (
          <Box
            key={tag.label}
            flex={{gap: 4, alignItems: 'center'}}
            data-tooltip={reduceText ? text : undefined}
            onClick={tag.onClick}
            style={{
              background:
                reduceColor && reduceText ? Colors.White : reduceColor ? Colors.Gray100 : color,
              color: reduceColor ? Colors.Gray700 : textcolor,
              fontWeight: reduceColor ? 500 : 700,
            }}
          >
            {known?.icon && (
              <OpTagIconWrapper
                role="img"
                $size={16}
                $img={known?.icon}
                $color={reduceColor ? (known?.reversed ? Colors.Gray900 : color) : textcolor}
                //$color={reduceColor ? color : textcolor}
                $rotation={null}
                aria-label={tag.label}
              />
            )}
            {known?.icon && reduceText ? undefined : text}
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
