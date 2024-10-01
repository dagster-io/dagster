import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {featureEnabled} from '../app/Flags';

export function getRunFeedPath() {
  return featureEnabled(FeatureFlag.flagRunsFeed) ? `/runs/` : `/runs-feed/`;
}

export function getBackfillPath(id: string) {
  // THis is hacky but basically we're dark launching runs-feed, so if we're on the runs-feed path, stay on it.
  if (location.pathname.includes('runs-feed')) {
    return `/runs-feed/b/${id}?tab=runs`;
  }
  return featureEnabled(FeatureFlag.flagRunsFeed)
    ? `/runs/b/${id}?tab=runs`
    : `/overview/backfills/${id}`;
}
