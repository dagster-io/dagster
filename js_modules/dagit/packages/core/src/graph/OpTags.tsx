import {Colors, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import airbyte from './optag-images/airbyte.svg';
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

interface IOpTagsProps {
  style: React.CSSProperties;
  minified: boolean;
  tags: IOpTag[];
}

const KNOWN_TAGS = {
  jupyter: {color: '#4E4E4E', content: <img src={jupyter} alt="Jupyter logo" role="img" />},
  ipynb: {color: '#4E4E4E', content: <img src={jupyter} alt="Jupyter logo" role="img" />},
  noteable: {color: '#00D2D2', content: <img src={noteable} alt="Noteable logo" role="img" />},
  airbyte: {color: '#655CFC', content: <img src={airbyte} alt="Airbyte logo" role="img" />},
  snowflake: {color: '#29B5E8', content: <img src={snowflake} alt="Snowflake logo" role="img" />},
  python: {color: '#35668F', content: <img src={python} alt="Python logo" role="img" />},
  fivetran: {color: '#0073FF', content: <img src={fivetran} alt="Fivetran logo" role="img" />},
  dbt: {color: '#FF6B4C', content: <img src={dbt} alt="dbt logo" role="img" />},
  slack: {color: '#4A144A', content: <img src={slack} alt="Slack logo" role="img" />},
  pytorch: {color: '#EE4C2C', content: <img src={pytorch} alt="pytorch logo" role="img" />},
  pyspark: {color: '#C74D15', content: <img src={pyspark} alt="pyspark logo" role="img" />},
  duckdb: {color: '#FCBC41', content: <img src={duckdb} alt="duckdb logo" role="img" />},
  tensorflow: {
    color: '#FE9413',
    content: <img src={tensorflow} alt="tensorflow logo" role="img" />,
  },
  pandas: {color: '#130754', content: <img src={pandas} alt="pandas logo" role="img" />},
  googlesheets: {
    color: '#23A566',
    content: <img src={googlesheets} alt="googlesheets logo" role="img" />,
  },
  sql: {
    color: '#B821FF',
    content: <img src={sql} alt="sql logo" role="img" />,
  },
  Expand: {color: '#D7A540', content: 'Expand'},
};

function generateColorForLabel(label = '') {
  return `hsl(${
    label
      .split('')
      .map((c) => c.charCodeAt(0))
      .reduce((n, a) => n + a) % 360
  }, 75%, 45%)`;
}

export const OpTags = React.memo(({tags, style, minified}: IOpTagsProps) => {
  return (
    <OpTagsContainer style={style} $minified={minified}>
      {tags.map((tag) => (
        <div
          key={tag.label}
          style={{background: KNOWN_TAGS[tag.label]?.color || generateColorForLabel(tag.label)}}
          onClick={tag.onClick}
        >
          {KNOWN_TAGS[tag.label]?.content || tag.label}
        </div>
      ))}
    </OpTagsContainer>
  );
});

const OpTagsContainer = styled.div<{$minified: boolean}>`
  gap: 6px;
  position: absolute;
  display: flex;

  & > div {
    padding: 0 8px;
    min-height: 24px;
    display: flex;
    align-items: center;
    color: ${Colors.White};
    font-family: ${FontFamily.default};
    font-size: 12px;
    font-weight: 700;
    border-radius: 8px;
  }
`;
