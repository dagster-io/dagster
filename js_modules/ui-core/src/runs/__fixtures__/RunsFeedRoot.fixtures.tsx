import {buildPartitionBackfill, buildPipelineTag, buildRun} from '../../graphql/builders';
import {RunStatus, RunsFeedView} from '../../graphql/types';
import {BackfillTableFragmentCompletedAssetJob} from '../../instance/backfill/__fixtures__/BackfillTable.fixtures';
import {buildQueryMock} from '../../testing/mocking';
import {DagsterTag} from '../RunTag';
import {RunsFeedRootQuery, RunsFeedRootQueryVariables} from '../types/useRunsFeedEntries.types';
import {RUNS_FEED_ROOT_QUERY} from '../useRunsFeedEntries';

export const RunsFeedRootMockRuns = buildQueryMock<RunsFeedRootQuery, RunsFeedRootQueryVariables>({
  query: RUNS_FEED_ROOT_QUERY,
  variables: {filter: {}, limit: 30, view: RunsFeedView.ROOTS},
  data: {
    runsFeedOrError: {
      __typename: 'RunsFeedConnection',
      cursor: 'iure',
      hasMore: false,
      results: [
        // No backfill, non-partitioned
        addPreviewSelectionToRun(
          buildRun({
            jobName: 'simple',
            tags: [buildPipelineTag({key: DagsterTag.FromUI, value: 'true'})],
            runStatus: RunStatus.SUCCESS,
          }),
        ),
        // No backfill, partitioned
        addPreviewSelectionToRun(
          buildRun({
            jobName: 'partitioned',
            tags: [
              buildPipelineTag({key: DagsterTag.Partition, value: '2020-01-01'}),
              buildPipelineTag({key: DagsterTag.FromUI, value: 'true'}),
            ],
            runStatus: RunStatus.SUCCESS,
          }),
        ),
        // Backfill, partitioned
        addPreviewSelectionToRun(
          buildRun({
            jobName: 'backfill_partitioned',
            tags: [
              buildPipelineTag({key: DagsterTag.Backfill, value: 'abcd'}),
              buildPipelineTag({key: DagsterTag.Partition, value: '2020-01-01'}),
              buildPipelineTag({key: DagsterTag.FromUI, value: 'true'}),
            ],
            runStatus: RunStatus.SUCCESS,
          }),
        ),
      ],
    },
  },
});

export const RunsFeedRootMockBackfill = buildQueryMock<
  RunsFeedRootQuery,
  RunsFeedRootQueryVariables
>({
  query: RUNS_FEED_ROOT_QUERY,
  variables: {filter: {}, limit: 30, view: RunsFeedView.ROOTS},
  data: {
    runsFeedOrError: {
      __typename: 'RunsFeedConnection',
      cursor: '',
      hasMore: false,
      results: [
        addStatusToPartitionBackfill(
          buildPartitionBackfill(BackfillTableFragmentCompletedAssetJob),
        ),
      ],
    },
  },
});

function addStatusToPartitionBackfill(backfill: ReturnType<typeof buildPartitionBackfill>) {
  return {
    ...backfill,
    backfillStatus: backfill.status,
  };
}

// The feed fragment aliases the bounded selection fields (assetSelection -> assetSelectionPreview,
// etc.); mock builders emit the un-aliased names, so map them across here.
function addPreviewSelectionToRun(run: ReturnType<typeof buildRun>) {
  return {
    ...run,
    assetSelectionPreview: run.assetSelection,
    assetCheckSelectionPreview: run.assetCheckSelection,
  };
}
