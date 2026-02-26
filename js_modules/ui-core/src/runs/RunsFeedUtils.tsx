export const RUNS_FEED_CURSOR_KEY = `runs_before`;

export function getBackfillPath(id: string, tab?: 'runs') {
  return tab ? `/runs/b/${id}?tab=${tab}` : `/runs/b/${id}`;
}
