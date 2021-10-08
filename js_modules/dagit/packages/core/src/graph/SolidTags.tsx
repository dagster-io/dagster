import * as React from 'react';

import {FontFamily} from '../ui/styles';

export interface ISolidTag {
  label: string;
  onClick: (e: React.MouseEvent) => void;
}

interface ISolidTagsProps {
  y: number;
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
  return (
    text
      .split('')
      .map((c) => c.charCodeAt(0))
      .reduce((n, a) => n + a) % 360
  );
}

const SolidTagsInner: React.FunctionComponent<ISolidTagsProps> = ({tags, y, minified}) => {
  const height = minified ? 32 : 20;

  return (
    <div style={{position: 'absolute', left: 0, top: y, display: 'flex', gap: 6}}>
      {tags.map((tag) => SVGNodeTag({tag, minified, height}))}
    </div>
  );
};

export const SVGNodeTag: React.FC<{tag: ISolidTag; minified: boolean; height: number}> = ({
  tag,
  minified,
  height,
}) => {
  const hue = hueForTag(tag.label);
  return (
    <div
      key={tag.label}
      style={{
        padding: minified ? 8 : 4,
        height,
        color: `hsl(${hue}, 75%, 50%)`,
        fontFamily: FontFamily.monospace,
        fontSize: minified ? 24 : 14,
        background: `hsl(${hue}, 10%, 95%)`,
        border: `1px solid hsl(${hue}, 75%, 50%)`,
      }}
      onClick={tag.onClick}
    >
      {tag.label}
    </div>
  );
};

export const SolidTags = React.memo(SolidTagsInner);
