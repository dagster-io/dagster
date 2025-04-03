import {RunsFeedView, buildRunsFeedConnection} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {RunsFeedRootQuery, RunsFeedRootQueryVariables} from '../types/useRunsFeedEntries.types';
import {RUNS_FEED_ROOT_QUERY} from '../useRunsFeedEntries';

export const RunsFeedRootMock = buildQueryMock<RunsFeedRootQuery, RunsFeedRootQueryVariables>({
  query: RUNS_FEED_ROOT_QUERY,
  variables: {filter: {}, limit: 30, view: RunsFeedView.ROOTS},
  data: {
    hasMore: false,
    runsFeedOrError: buildRunsFeedConnection({
      results: [
        // Apollo is stripping everything but __typename + id out of these objects,
        // and it seems generally it does not support the vardic type well. (Run | PartitionBackfill)
        //
        // buildRun({
        //   id: 'a0',
        //   tags: [
        //     buildPipelineTag({
        //       key: DagsterTag.Partition,
        //       value: '5',
        //     }),
        //     buildPipelineTag({
        //       key: DagsterTag.Backfill,
        //       value: 'abc123',
        //     }),
        //     buildPipelineTag({
        //       key: DagsterTag.SensorName,
        //       value: 's3_sensor',
        //     }),
        //     buildPipelineTag({
        //       key: 'snowflake_db',
        //       value: 'customers',
        //     }),
        //     buildPipelineTag({
        //       key: 'team',
        //       value: 'sales',
        //     }),
        //     buildPipelineTag({
        //       key: 'job',
        //       value: 'cloud_analytics',
        //     }),
        //     buildPipelineTag({
        //       key: 'max_run_time',
        //       value: '2700',
        //     }),
        //     buildPipelineTag({
        //       key: 'automated',
        //       value: 'true',
        //     }),
        //   ],
        // }),
        // buildPartitionBackfill({id: 'b1'}),
      ],
    }),
  },
});
