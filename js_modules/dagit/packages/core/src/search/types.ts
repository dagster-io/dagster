export enum SearchResultType {
  Asset,
  Page,
  PartitionSet,
  Pipeline,
  Repository,
  Run,
  Schedule,
  Sensor,
  Solid,
}

export type SearchResult = {
  label: string;
  description: string;
  href: string;
  type: SearchResultType;
  tags?: string;
};
