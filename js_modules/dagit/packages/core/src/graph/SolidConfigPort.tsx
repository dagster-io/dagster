import * as React from 'react';

import {ColorsWIP} from '../ui/Colors';

import {PipelineColorScale} from './PipelineColorScale';
import {SVGEllipseInRect} from './SVGComponents';

interface ISolidConfigPortProps {
  x: number;
  y: number;
  minified: boolean;
}

export const SolidConfigPort: React.SFC<ISolidConfigPortProps> = ({x, y, minified}) => {
  return <>{!minified ? 'Config' : 'C'}</>;
};
