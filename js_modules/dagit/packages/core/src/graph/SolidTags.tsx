import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';
import {FontFamily} from '../ui/styles';

export interface ISolidTag {
  label: string;
  onClick: (e: React.MouseEvent) => void;
}

interface ISolidTagsProps {
  style: React.CSSProperties;
  minified: boolean;
  tags: ISolidTag[];
}

function hueForTag(text = '') {
  if (text === 'ipynb') {
    return 25;
  }
  if (text === 'dbt') {
    return 250;
  }
  if (text === 'snowflake') {
    return 197;
  }
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

export const SolidTags = React.memo(({tags, style, minified}: ISolidTagsProps) => {
  return (
    <SolidTagsContainer style={style} $minified={minified}>
      {tags.map((tag) => (
        <div
          key={tag.label}
          style={{background: `hsl(${hueForTag(tag.label)}, 75%, 50%)`}}
          onClick={tag.onClick}
        >
          {tag.label}
        </div>
      ))}
    </SolidTagsContainer>
  );
});

const SolidTagsContainer = styled.div<{$minified: boolean}>`
  gap: 6px;
  position: absolute;
  display: flex;

  & > div {
    padding: 0 ${(p) => (p.$minified ? 10 : 5)}px;
    line-height: ${(p) => (p.$minified ? 32 : 20)}px;
    color: ${ColorsWIP.White};
    font-family: ${FontFamily.monospace};
    font-size: ${(p) => (p.$minified ? 24 : 14)}px;
    font-weight: 700;
    border-radius: 3px;
  }
`;
