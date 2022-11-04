import {Colors, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import airbyte_logo from './optag-images/airbyte_logo.svg';
import dbt_logo from './optag-images/dbt_logo.svg';
import fivetran_logo from './optag-images/fivetran_logo.svg';
import jupyter_logo from './optag-images/jupyter_logo.svg';
import noteable_logo from './optag-images/noteable_logo.svg';
import python_logo from './optag-images/python_logo.svg';
import snowflake_logo from './optag-images/snowflake_logo.svg';

export interface IOpTag {
  label: string;
  onClick: (e: React.MouseEvent) => void;
}

interface IOpTagsProps {
  style: React.CSSProperties;
  minified: boolean;
  tags: IOpTag[];
}

function hueForTag(text = '') {
  if (text === 'pyspark' || text === 'spark') {
    return 30;
  }
  if (text === 'Expand') {
    return 40;
  }
  return (
    text
      .split('')
      .map((c) => c.charCodeAt(0))
      .reduce((n, a) => n + a) % 360
  );
}

function getTag(tag: IOpTag) {
  if (tag.label === 'noteable') {
    return <img src={noteable_logo} alt="Noteable logo" role="img" />;
  } else if (tag.label === 'ipynb') {
    return <img src={jupyter_logo} alt="Jupyter logo" role="img" />;
  } else if (tag.label === 'airbyte') {
    return <img src={airbyte_logo} alt="Airbyte logo" role="img" />;
  } else if (tag.label === 'dbt') {
    return <img src={dbt_logo} alt="dbt logo" role="img" />;
  } else if (tag.label === 'fivetran') {
    return <img src={fivetran_logo} alt="Fivetran logo" role="img" />;
  } else if (tag.label === 'snowflake') {
    return <img src={snowflake_logo} alt="Snowflake logo" role="img" />;
  } else if (tag.label === 'python') {
    return <img src={python_logo} alt="Python logo" role="img" />;
  } else {
    return (
      <div
        key={tag.label}
        style={{background: `hsl(${hueForTag(tag.label)}, 75%, 50%)`}}
        onClick={tag.onClick}
      >
        {tag.label}
      </div>
    );
  }
}

export const OpTags = React.memo(({tags, style, minified}: IOpTagsProps) => {
  return (
    <OpTagsContainer style={style} $minified={minified}>
      {tags.map((tag) => getTag(tag))}
    </OpTagsContainer>
  );
});

const OpTagsContainer = styled.div<{$minified: boolean}>`
  gap: 6px;
  position: absolute;
  display: flex;

  & > div {
    padding: 0 ${(p) => (p.$minified ? 10 : 5)}px;
    line-height: ${(p) => (p.$minified ? 32 : 20)}px;
    color: ${Colors.White};
    font-family: ${FontFamily.monospace};
    font-size: ${(p) => (p.$minified ? 24 : 14)}px;
    font-weight: 700;
    border-radius: 3px;
  }
`;
