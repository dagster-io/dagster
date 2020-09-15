import {GraphQueryItem} from '../GraphQueryImpl';
import {IStepState} from '../RunMetadataProvider';

export type IGaantNode = GraphQueryItem;

export interface GaantViewport {
  left: number; // Note: pixel values
  top: number;
  width: number;
  height: number;
}

export interface GaantChartPlacement {
  key: string; // A React-friendly unique key like `step:retry-1`
  width: number;
  x: number; // Note: This is a pixel value
  y: number; // Note: This is a "row number" not a pixel value
}

export interface GaantChartBox extends GaantChartPlacement {
  state: IStepState | undefined;
  children: GaantChartBox[];
  node: IGaantNode;
  root: boolean;
}

export interface GaantChartMarker extends GaantChartPlacement {}

export interface GaantChartLayout {
  boxes: GaantChartBox[];

  // only present in timescaled layout
  markers: GaantChartMarker[];
}

export interface GaantChartLayoutOptions {
  mode: GaantChartMode;
  zoom: number; // 1 => 100
  hideWaiting: boolean;
  hideTimedMode: boolean;
  hideUnselectedSteps: boolean;
}

export enum GaantChartMode {
  FLAT = 'flat',
  WATERFALL = 'waterfall',
  WATERFALL_TIMED = 'waterfall-timed',
}

export const MIN_SCALE = 0.0002;
export const MAX_SCALE = 0.5;
export const LEFT_INSET = 5;
export const BOX_HEIGHT = 30;
export const BOX_MARGIN_Y = 5;
export const BOX_SPACING_X = 20;
export const BOX_WIDTH = 100;
export const BOX_DOT_WIDTH_CUTOFF = 8;
export const BOX_SHOW_LABEL_WIDTH_CUTOFF = 30;
export const BOX_DOT_SIZE = 6;
export const BOX_DOT_MARGIN_Y = (BOX_HEIGHT - BOX_DOT_SIZE) / 2;

export const LINE_SIZE = 2;
export const CSS_DURATION = 100;

export const DEFAULT_OPTIONS: GaantChartLayoutOptions = {
  mode: GaantChartMode.WATERFALL,
  hideWaiting: false,
  hideTimedMode: false,
  zoom: 1,
  hideUnselectedSteps: false,
};
