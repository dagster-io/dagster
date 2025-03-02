export const RUNS_FEED_CURSOR_KEY = `runs_before`;

export function getBackfillPath(id: string, _isAssetBackfill: boolean) {
  return `/runs/b/${id}`;
}
