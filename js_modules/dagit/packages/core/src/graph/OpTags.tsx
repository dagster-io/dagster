import {Box, Colors, FontFamily, IconWrapper} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import airbyte from './optag-images/airbyte.svg';
import databricks from './optag-images/databricks.svg';
import dbt from './optag-images/dbt.svg';
import duckdb from './optag-images/duckdb.svg';
import fivetran from './optag-images/fivetran.svg';
import googlesheets from './optag-images/googlesheets.svg';
import jupyter from './optag-images/jupyter.svg';
import noteable from './optag-images/noteable.svg';
import pandas from './optag-images/pandas.svg';
import pyspark from './optag-images/pyspark.svg';
import python from './optag-images/python.svg';
import pytorch from './optag-images/pytorch.svg';
import slack from './optag-images/slack.svg';
import snowflake from './optag-images/snowflake.svg';
import sql from './optag-images/sql.svg';
import tensorflow from './optag-images/tensorflow.svg';

export interface IOpTag {
  label: string;
  onClick: (e: React.MouseEvent) => void;
}

interface OpTagsProps {
  style: React.CSSProperties;
  tags: IOpTag[];
  reduceColor?: boolean;
  reduceText?: boolean;
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
  databricks: {
    color: '#FD3820',
    icon: databricks,
    content: 'Databricks',
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
        const known = KNOWN_TAGS[coerceToStandardLabel(tag.label)];
        const text = known?.content || tag.label;
        const color = known?.color || generateColorForLabel(tag.label);

        return (
          <Box
            key={tag.label}
            flex={{gap: 4, alignItems: 'center'}}
            data-tooltip={reduceText ? text : undefined}
            onClick={tag.onClick}
            style={{
              background: reduceColor ? Colors.Gray100 : color,
              color: reduceColor ? Colors.Gray700 : Colors.White,
              fontWeight: reduceColor ? 500 : 700,
            }}
          >
            {known?.icon && (
              <OpTagIconWrapper
                role="img"
                $size={16}
                $img={known?.icon}
                $color={reduceColor ? color : 'white'}
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
