export interface AssetKey {
  path: string[];
}

export type AssetLineageScope = 'neighbors' | 'upstream' | 'downstream';

export interface AssetViewParams {
  view?: string;
  lineageScope?: AssetLineageScope;
  lineageDepth?: number;
  partition?: string;
  time?: string;
  asOf?: string;
  evaluation?: string;
}
