import {Colors} from '@blueprintjs/core';
import {scaleOrdinal} from '@vx/scale';

export const PipelineColorScale = scaleOrdinal({
  domain: [
    'source',
    'input',
    'inputHighlighted',
    'solid',
    'solidComposite',
    'solidCompositeChild',
    'solidDarker',
    'output',
    'outputHighlighted',
    'materializations',
  ],
  range: [
    Colors.TURQUOISE5,
    Colors.TURQUOISE3,
    Colors.TURQUOISE1,
    '#DBE6EE',
    '#E6DBEE',
    '#E0E0ED',
    '#7D8C97',
    Colors.BLUE3,
    Colors.BLUE1,
    Colors.ORANGE5,
  ],
});
