import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {runsPathWithFilters} from './RunsFilterInput';
import {featureEnabled} from '../app/Flags';

export const RUNS_FEED_CURSOR_KEY = `runs_before`;

export function getBackfillPath(id: string, isAssetBackfill: boolean) {
  if (featureEnabled(FeatureFlag.flagLegacyRunsPage)) {
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
  return `/runs/b/${id}`;
}
