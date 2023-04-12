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

export type SearchResult = {
  label: string;
  description: string;
  href: string;
  type: SearchResultType;
  tags?: string;
};
