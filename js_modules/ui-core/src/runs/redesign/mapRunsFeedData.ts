import {RunStatus} from '../../graphql/types';
import {doneStatuses} from '../RunStatuses';
import {getBackfillPath} from '../RunsFeedUtils';
import {
  RunSelectionDetailsFragment,
  RunSummaryFragment,
  RunsFeedEntryFragment,
} from './types/RunsFeedFragments.types';

type SelectionPreview<T> = {preview: T[]; count: number; complete: boolean} | null;

const getSelectionPreview = <T>(preview: T[] | null, count: number): SelectionPreview<T> => {
  if (preview === null || count < preview.length || (preview.length === 0 && count !== 0)) {
    return null;
  }
  return {preview, count, complete: preview.length === count};
};

const getTiming = (entry: RunsFeedEntryFragment) => {
  let startAtMs = entry.startTime === null ? null : entry.startTime * 1000;
  const endAtMs = entry.endTime === null ? null : entry.endTime * 1000;
  if (
    entry.__typename === 'Run' &&
    doneStatuses.has(entry.runStatus) &&
    entry.startTime === entry.endTime
  ) {
    // GraphQL can substitute a missing Run start time with its end time.
    startAtMs = null;
  }
  return {
    createdAtMs: entry.creationTime * 1000,
    startAtMs,
    endAtMs,
    durationMs: startAtMs === null || endAtMs === null ? null : Math.max(0, endAtMs - startAtMs),
  };
};

const FALSY_WILL_RETRY_VALUES = ['', 'false', 'none', '0'];

const getWillRetry = (run: RunSummaryFragment) => {
  const value = run.tags.find(({key}) => key === 'dagster/will_retry')?.value;
  return (
    run.runStatus === RunStatus.FAILURE &&
    value !== undefined &&
    !FALSY_WILL_RETRY_VALUES.includes(value.toLowerCase()) &&
    !run.tags.some(({key}) => key === 'dagster/auto_retry_run_id')
  );
};

export const mapRunsFeedEntry = (entry: RunsFeedEntryFragment) => {
  switch (entry.__typename) {
    case 'Run':
      return {
        ...entry,
        href: `/runs/${entry.id}`,
        timing: getTiming(entry),
        selectionPreviews: {
          assets: getSelectionPreview(entry.assetSelectionPreview, entry.assetSelectionCount),
          checks: getSelectionPreview(
            entry.assetCheckSelectionPreview,
            entry.assetCheckSelectionCount,
          ),
        },
        isAutomaticRetry: entry.tags.some(({key}) => key === 'dagster/retry_number'),
        willRetry: getWillRetry(entry),
      };
    case 'PartitionBackfill':
      return {
        ...entry,
        href: getBackfillPath(entry.id),
        timing: getTiming(entry),
        selectionPreviews: null,
      };
  }
};

export const mapRunSelectionDetails = (detail: RunSelectionDetailsFragment) => {
  const selectedAssetPaths =
    detail.assetSelection === null
      ? null
      : new Set(detail.assetSelection.map(({path}) => JSON.stringify(path)));
  const annotatedChecks =
    detail.assetCheckSelection?.map((check) => {
      const assetIsSelected =
        selectedAssetPaths === null
          ? null
          : selectedAssetPaths.has(JSON.stringify(check.assetKey.path));
      return {...check, assetIsSelected};
    }) ?? null;

  return {...detail, annotatedChecks};
};

export type MappedRunsFeedEntry = ReturnType<typeof mapRunsFeedEntry>;
export type MappedRunSelectionDetails = ReturnType<typeof mapRunSelectionDetails>;
