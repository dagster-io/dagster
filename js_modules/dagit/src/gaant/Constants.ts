import { GraphQueryItem } from "../GraphQueryImpl";

export type IGaantNode = GraphQueryItem;

export interface GaantChartBox {
  children: GaantChartBox[];
  node: IGaantNode;
  width: number;
  x: number;
  y: number;

  // the X initial position of this box determined by the layout algorithm
  // (before run metadata is applied) necessary to enforce the gaant arrow
  // direction.
  minX: number;
}

export interface GaantChartLayout {
  roots: GaantChartBox[];
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
export const BOX_DOT_WIDTH_CUTOFF = 8;
export const BOX_SHOW_LABEL_WIDTH_CUTOFF = 30;
export const BOX_DOT_SIZE = 6;

export const LINE_SIZE = 2;
export const CSS_DURATION = `100ms`;

export const DEFAULT_OPTIONS: GaantChartLayoutOptions = {
  mode: GaantChartMode.WATERFALL,
  hideWaiting: false,
  hideTimedMode: false,
  scale: 0.15
};
