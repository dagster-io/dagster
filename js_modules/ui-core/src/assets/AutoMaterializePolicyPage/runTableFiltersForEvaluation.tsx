import {RunsFilter} from '../../graphql/types';

const BACKFILL_ID_LENGTH = 8;

/**
 * For a single asset for a single tick, DA will either request a list of runs or a single backfill.
 * When DA requests a backfill we want to show a row for that backfill in the table, so we need to
 * construct the RunsFilter differently. Backfill IDs are 8 characters long, so we can use that to
 * determine if a backfill was requested. If DA is updated to request multiple backfills in a
 * single evaluation, or emit a combination of runs and backfills in a single evaluation, this
 * logic will need to be updated.
 */
export const runTableFiltersForEvaluation = (runIds: string[]): RunsFilter | null => {
  const firstRunId = runIds[0];
  if (firstRunId) {
    if (firstRunId.length === BACKFILL_ID_LENGTH) {
      return {tags: [{key: 'dagster/backfill', value: firstRunId}]};
    }
    return {runIds};
  }
  return null;
};
