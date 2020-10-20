export enum SearchResultType {
  Asset,
  Page,
  Pipeline,
  Repository,
  Run,
  Schedule,
  Solid,
}

export type SearchResult = {
  key: string;
  label: string;
  description: string;
  href: string;
  type: SearchResultType;
  tags?: string;
};
