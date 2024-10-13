import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {runsPathWithFilters} from './RunsFilterInput';
import {featureEnabled} from '../app/Flags';

export function getRunFeedPath() {
  return featureEnabled(FeatureFlag.flagRunsFeed) ? `/runs/` : `/runs-feed/`;
}

export function getBackfillPath(id: string, isAssetBackfill: boolean) {
  // THis is hacky but basically we're dark launching runs-feed, so if we're on the runs-feed path, stay on it.
  if (location.pathname.includes('runs-feed')) {
    return `/runs-feed/b/${id}?tab=runs`;
  }

  if (featureEnabled(FeatureFlag.flagRunsFeed)) {
    return `/runs/b/${id}?tab=runs`;
  }
  if (isAssetBackfill) {
    return `/overview/backfills/${id}`;
  }
  return runsPathWithFilters([
    {
      token: 'tag',
      value: `dagster/backfill=${id}`,
    },
  ]);
}
