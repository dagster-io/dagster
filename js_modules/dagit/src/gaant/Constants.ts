import { GraphQueryItem } from "../GraphQueryImpl";

export type IGaantNode = GraphQueryItem;

export interface GaantChartBox {
  children: GaantChartBox[];
  node: IGaantNode;
  x: number;
  width: number;
  y: number;
}

export interface GaantChartLayout {
  boxes: GaantChartBox[];
}

export interface GaantChartLayoutOptions {
  mode: GaantChartMode;
  scale: number;
  hideWaiting: boolean;
  hideTimedMode: boolean;
}

export enum GaantChartMode {
  FLAT = "flat",
  WATERFALL = "waterfall",
  WATERFALL_TIMED = "waterfall-timed"
}

export const MIN_SCALE = 0.005;
export const MAX_SCALE = 0.5;
export const LEFT_INSET = 5;
export const BOX_HEIGHT = 30;
export const BOX_MARGIN_Y = 5;
export const BOX_SPACING_X = 20;
export const BOX_WIDTH = 100;
export const BOX_MIN_WIDTH = 6;
export const LINE_SIZE = 2;
export const CSS_DURATION = `100ms`;

export const DEFAULT_OPTIONS: GaantChartLayoutOptions = {
  mode: GaantChartMode.WATERFALL,
  hideWaiting: false,
  hideTimedMode: false,
  scale: 0.15
};
