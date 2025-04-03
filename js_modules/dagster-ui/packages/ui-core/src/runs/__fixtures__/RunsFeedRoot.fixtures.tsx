import {RunsFeedView} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {RunsFeedRootQuery, RunsFeedRootQueryVariables} from '../types/useRunsFeedEntries.types';
import {RUNS_FEED_ROOT_QUERY} from '../useRunsFeedEntries';

export const RunsFeedRootMock = buildQueryMock<RunsFeedRootQuery, RunsFeedRootQueryVariables>({
  query: RUNS_FEED_ROOT_QUERY,
  variables: {filter: {}, limit: 30, view: RunsFeedView.ROOTS},
  data: {
    runsFeedOrError: {
      __typename: 'RunsFeedConnection',
      cursor: 'iure',
      hasMore: false,
      results: [
        // Apollo is stripping everything but __typename + id out of these objects,
        // It seems generally confused because this is a vardic type (Run | PartitionBackfill)
        // that also remaps the status property of backfills to `backfillStatus`.
        //
        // buildRun({
        //   id: 'a0',
        //   tags: [
        //     buildPipelineTag({key: DagsterTag.Partition, value: '5'}),
        //     buildPipelineTag({key: DagsterTag.Backfill, value: 'abc123'}),
        //     buildPipelineTag({key: DagsterTag.SensorName, value: 's3_sensor'}),
        //   ],
        // }),
        // {...buildPartitionBackfill({id: 'b1'}), backfillStatus: BulkActionStatus.REQUESTED},
      ],
    },
  },
});
