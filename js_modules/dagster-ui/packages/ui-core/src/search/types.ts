import Fuse from 'fuse.js';

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
  ComputeKind = 'AssetFilterSearchResultType.ComputeKind',
  CodeLocation = 'AssetFilterSearchResultType.CodeLocation',
  Owner = 'AssetFilterSearchResultType.Owner',
  AssetGroup = 'AssetFilterSearchResultType.AssetGroup',
}

export function isAssetFilterSearchResultType(
  type: SearchResultType | AssetFilterSearchResultType,
): type is AssetFilterSearchResultType {
  return (
    type === AssetFilterSearchResultType.AssetGroup ||
    type === AssetFilterSearchResultType.CodeLocation ||
    type === AssetFilterSearchResultType.ComputeKind ||
    type === AssetFilterSearchResultType.Owner
  );
}

export type SearchResult = {
  label: string;
  description: string;
  href: string;
  type: SearchResultType | AssetFilterSearchResultType;
  tags?: string;
  numResults?: number;
};

export type ReadyResponse = {type: 'ready'};
export type ResultResponse = {
  type: 'results';
  queryString: string;
  results: Fuse.FuseResult<SearchResult>[];
};

export type WorkerSearchResponse = ReadyResponse | ResultResponse;
