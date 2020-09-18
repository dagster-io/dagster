import * as React from 'react';

import {SVGFlowLayoutFiller, SVGFlowLayoutRect, SVGMonospaceText} from './SVGComponents';

export interface ISolidTag {
  label: string;
  onClick: (e: React.MouseEvent) => void;
}

interface ISolidTagsProps {
  x: number;
  y: number;
  width: number;
  minified: boolean;
  tags: ISolidTag[];
}

function hueForTag(text = '') {
  if (text === 'ipynb') return 25;
  if (text === 'snowflake') return 197;
  if (text === 'pyspark' || text === 'spark') return 30;
  return (
    text
      .split('')
      .map((c) => c.charCodeAt(0))
      .reduce((n, a) => n + a) % 360
  );
}

const SolidTags: React.FunctionComponent<ISolidTagsProps> = ({tags, x, y, width, minified}) => {
  const height = minified ? 32 : 20;
  const overhang = 10;

  return (
    <SVGFlowLayoutRect
      x={x}
      y={y - (height - overhang)}
      width={width}
      height={height}
      fill={'transparent'}
      stroke={'transparent'}
      spacing={minified ? 8 : 4}
      padding={0}
    >
      <SVGFlowLayoutFiller />
      {tags.map((tag) => {
        const hue = hueForTag(tag.label);
        return (
          <SVGFlowLayoutRect
            key={tag.label}
            rx={0}
            ry={0}
            height={height}
            padding={minified ? 8 : 4}
            fill={`hsl(${hue}, 10%, 95%)`}
            stroke={`hsl(${hue}, 75%, 50%)`}
            onClick={tag.onClick}
            strokeWidth={1}
            spacing={0}
          >
            <SVGMonospaceText
              text={tag.label}
              fill={`hsl(${hue}, 75%, 50%)`}
              size={minified ? 24 : 14}
            />
          </SVGFlowLayoutRect>
        );
      })}
    </SVGFlowLayoutRect>
  );
};

export default React.memo(SolidTags);
