import Fuse from 'fuse.js';

import {AssetTableFragment} from '../assets/types/AssetTableFragment.types';
import {AssetKey, DefinitionTag} from '../graphql/types';
import {ResourceEntryFragment} from '../resources/types/WorkspaceResourcesQuery.types';
import {
  WorkspaceAssetGroupFragment,
  WorkspacePartitionSetFragment,
  WorkspacePipelineFragment,
  WorkspaceScheduleFragment,
  WorkspaceSensorFragment,
} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

export enum SearchResultType {
  AssetGroup,
  Asset,
  Page,
  PartitionSet,
  Pipeline,
  Repository,
  Run,
  Schedule,
  Sensor,
  Solid,
  Resource,
}

export enum AssetFilterSearchResultType {
  // Add types with corresponding strings to distinguish
  // between SearchResultType.AssetGroup
  Kind = 'kind:',
  Tag = 'tag:',
  CodeLocation = 'code_location:',
  Owner = 'owner:',
  AssetGroup = 'asset_group:',
  Column = 'column:',
  ColumnTag = 'column_tag:',
  TableName = 'table_name:',
}

export function isAssetFilterSearchResultType(
  type: SearchResultType | AssetFilterSearchResultType,
): type is AssetFilterSearchResultType {
  return (
    type === AssetFilterSearchResultType.AssetGroup ||
    type === AssetFilterSearchResultType.CodeLocation ||
    type === AssetFilterSearchResultType.Kind ||
    type === AssetFilterSearchResultType.Owner ||
    type === AssetFilterSearchResultType.Tag ||
    type === AssetFilterSearchResultType.Column ||
    type === AssetFilterSearchResultType.ColumnTag ||
    type === AssetFilterSearchResultType.TableName
  );
}

export type SearchResult = {
  key?: AssetKey;
  label: string;
  description: string;
  href: string;
  type: SearchResultType | AssetFilterSearchResultType;
  tags?: DefinitionTag[];
  kinds?: string[];
  numResults?: number;
  repoPath?: string;
  node?:
    | null
    | AssetTableFragment
    | WorkspaceAssetGroupFragment
    | WorkspacePipelineFragment
    | WorkspaceScheduleFragment
    | WorkspaceSensorFragment
    | WorkspacePartitionSetFragment
    | ResourceEntryFragment;
};

export type ReadyResponse = {type: 'ready'};
export type ResultResponse = {
  type: 'results';
  queryString: string;
  results: Fuse.FuseResult<SearchResult>[];
};

export type WorkerSearchResponse = ReadyResponse | ResultResponse;
