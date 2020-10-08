import {Colors} from '@blueprintjs/core';
import * as React from 'react';

import {PipelineColorScale} from 'src/graph/PipelineColorScale';
import {SVGEllipseInRect} from 'src/graph/SVGComponents';

interface ISolidConfigPortProps {
  x: number;
  y: number;
  minified: boolean;
}

export const SolidConfigPort: React.SFC<ISolidConfigPortProps> = ({x, y, minified}) => {
  return (
    <>
      <SVGEllipseInRect
        x={x}
        y={y}
        width={26}
        height={26}
        stroke={Colors.GRAY3}
        fill={PipelineColorScale('solid')}
        pathLength={100}
        strokeWidth={1}
        strokeDasharray={`0 50 0`}
      />
      <SVGEllipseInRect
        x={x + 3}
        y={y + 3}
        width={20}
        height={20}
        stroke={Colors.WHITE}
        fill={PipelineColorScale('solidDarker')}
        pathLength={100}
        strokeWidth={2}
      />
      {!minified && (
        <text
          x={x + 8}
          y={y + 7.5}
          style={{font: `14px "Arial", san-serif`}}
          fill={Colors.WHITE}
          dominantBaseline="hanging"
        >
          C
        </text>
      )}
    </>
  );
};
