import {ColorName} from './ColorName';
import {CoreColors} from './CoreColors';
import {DataVizColors} from './DataVizColors';
import {TranslucentColors} from './TranslucentColors';

export type Theme = Record<
  ColorName,
  keyof typeof CoreColors | keyof typeof TranslucentColors | keyof typeof DataVizColors
>;
