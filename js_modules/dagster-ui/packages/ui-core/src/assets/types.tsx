import {AssetViewDefinitionQuery} from './types/AssetView.types';

export interface AssetKey {
  path: string[];
}

export type AssetDefinition = Extract<
  AssetViewDefinitionQuery['assetOrError'],
  {__typename: 'Asset'}
>['definition'];

export type AssetLineageScope = 'neighbors' | 'upstream' | 'downstream';

export interface AssetViewParams {
  view?: string;
  lineageScope?: AssetLineageScope;
  lineageDepth?: number;
  partition?: string;
  time?: string;
  asOf?: string;
  evaluation?: string;
  checkDetail?: string;
  default_range?: string;
  column?: string;
}
