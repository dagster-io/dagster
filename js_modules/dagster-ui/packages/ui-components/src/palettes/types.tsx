import {ColorName} from './ColorName';
import {CoreColors, TranslucentColors} from './Colors';

export type Theme = Record<ColorName, keyof typeof CoreColors | keyof typeof TranslucentColors>;
