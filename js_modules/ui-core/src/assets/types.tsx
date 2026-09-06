import {AssetViewDefinitionQuery} from './types/AssetView.types';

export interface AssetKey {
  path: string[];
}

export type AssetDefinition = Extract<
  AssetViewDefinitionQuery['assetOrError'],
  {__typename: 'Asset'}
>['definition'];

export type AssetLineageScope = 'neighbors' | 'upstream' | 'downstream';

// The set of valid values for the `view` query param on the asset details page. These
// correspond to the tabs rendered in `AssetView` (plus the cloud-only `insights` and
// `change-history` tabs handled by `renderFeatureView`, and the `folder` catalog view).
export type AssetViewTab =
  | 'overview'
  | 'lineage'
  | 'partitions'
  | 'events'
  | 'automation'
  | 'checks'
  | 'insights'
  | 'change-history'
  | 'folder';

export type AssetViewParams = {
  view?: AssetViewTab;
  lineageScope?: AssetLineageScope;
  lineageDepth?: number;
  partition?: string;
  time?: string;
  asOf?: string;
  evaluation?: string;
  checkDetail?: string;
  default_range?: string;
  column?: string;
  showAllEvents?: boolean;
  status?: string;
  'asset-selection'?: string;
};
