import {Colors} from '@dagster-io/ui-components';

import {colorForString} from '../ui/colorForString';

export const orderedColors = [
  Colors.dataVizBlurple(),
  Colors.dataVizRed(),
  Colors.dataVizCyan(),
  Colors.dataVizViolet(),
  Colors.dataVizBlue(),
  Colors.dataVizPink(),
  Colors.dataVizGreen(),
  Colors.dataVizYellow(),
  Colors.dataVizTeal(),
  Colors.dataVizOrange(),
  Colors.dataVizLime(),
  Colors.dataVizBrown(),
  Colors.dataVizGray(),
  Colors.dataVizGrayAlt(),
  Colors.dataVizBlurpleAlt(),
  Colors.dataVizRedAlt(),
  Colors.dataVizCyanAlt(),
  Colors.dataVizVioletAlt(),
  Colors.dataVizBlueAlt(),
  Colors.dataVizPinkAlt(),
  Colors.dataVizGreenAlt(),
  Colors.dataVizYellowAlt(),
  Colors.dataVizTealAlt(),
  Colors.dataVizOrangeAlt(),
  Colors.dataVizLimeAlt(),
  Colors.dataVizBrownAlt(),
];

export const insightsColorForString = colorForString(orderedColors);
