import {Box} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetCheckTagCollection, AssetKeyTagCollection} from './AssetTagCollections';
import {RUN_FEED_TARGET_ASSET_SELECTION_QUERY} from './RunTargetLinkQuery';
import {useLazyQuery} from '../apollo-client';
import {
  RunFeedTargetAssetSelectionQuery,
  RunFeedTargetAssetSelectionQueryVariables,
} from './types/RunTargetLinkQuery.types';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {Check} from '../assets/AssetListUtils';
import {AssetKey} from '../assets/types';
import {PipelineTag} from '../pipelines/PipelineReference';
import {RepoAddress} from '../workspace/types';

// The *Preview selections are bounded (see RunsFeedTableEntryFragment); the run also carries the
// untruncated counts, and the full lists are fetched on demand (see
// RUN_FEED_TARGET_ASSET_SELECTION_QUERY).
type RunTargetLinkRun = {
  id: string;
  pipelineName: string;
  assetSelectionPreview: AssetKey[] | null;
  assetSelectionCount: number;
  assetCheckSelectionPreview: Check[] | null;
  assetCheckSelectionCount: number;
};

interface Props {
  run: RunTargetLinkRun;
  repoAddress: RepoAddress | null;
  extraTags?: React.ReactNode[];
}

export const RunTargetLink = ({run, repoAddress, extraTags}: Props) => {
  const isAssetRun = isHiddenAssetGroupJob(run.pipelineName);

  const [fetchFullSelection, {data, loading}] = useLazyQuery<
    RunFeedTargetAssetSelectionQuery,
    RunFeedTargetAssetSelectionQueryVariables
  >(RUN_FEED_TARGET_ASSET_SELECTION_QUERY, {variables: {runId: run.id}});

  // The popover's onOpening fires on every hover, so guard with a ref to fetch exactly once per
  // mounted row (a synchronous ref, not Apollo's async `called`, so rapid re-hovers can't slip
  // through before a re-render).
  const requestedRef = React.useRef(false);
  const onRequestFullSelection = React.useCallback(() => {
    if (!requestedRef.current) {
      requestedRef.current = true;
      void fetchFullSelection();
    }
  }, [fetchFullSelection]);

  const full = data?.runOrError.__typename === 'Run' ? data.runOrError : null;

  // The bounded preview of the asset selection (the full list is loaded lazily); null when this
  // run isn't an asset-group-job run, in which case we render the job tag instead.
  const previewAssetKeys = React.useMemo(
    () => (isAssetRun ? (run.assetSelectionPreview ?? []) : null),
    [isAssetRun, run.assetSelectionPreview],
  );

  if (previewAssetKeys) {
    return (
      <Box flex={{direction: 'column', gap: 4}}>
        <AssetKeyTagCollection
          assetKeys={previewAssetKeys}
          useTags
          extraTags={extraTags}
          maxRows={run.assetCheckSelectionCount ? 1 : 2}
          lazy={{
            totalCount: run.assetSelectionCount,
            allItems: full?.assetSelection ?? null,
            loading,
            onRequest: onRequestFullSelection,
          }}
        />
        <AssetCheckTagCollection
          assetChecks={run.assetCheckSelectionPreview}
          maxRows={run.assetSelectionCount ? 1 : 2}
          lazy={{
            totalCount: run.assetCheckSelectionCount,
            allItems: full?.assetCheckSelection ?? null,
            loading,
            onRequest: onRequestFullSelection,
          }}
        />
      </Box>
    );
  }
  return (
    <PipelineTag
      isJob
      showIcon
      pipelineName={run.pipelineName}
      pipelineHrefContext={repoAddress || 'repo-unknown'}
    />
  );
};
