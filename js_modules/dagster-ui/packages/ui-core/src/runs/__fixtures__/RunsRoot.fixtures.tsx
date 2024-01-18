import {buildQueryMock} from '../../assets/AutoMaterializePolicyPage/__fixtures__/AutoMaterializePolicyPage.fixtures';
import {buildPipelineTag, buildRun, buildRuns} from '../../graphql/types';
import {DagsterTag} from '../RunTag';
import {RUNS_ROOT_QUERY} from '../RunsRoot';
import {RunsRootQuery, RunsRootQueryVariables} from '../types/RunsRoot.types';

export const RunsRootMock = buildQueryMock<RunsRootQuery, RunsRootQueryVariables>({
  query: RUNS_ROOT_QUERY,
  variables: {filter: {}, limit: 26},
  data: {
    pipelineRunsOrError: buildRuns({
      count: 7,
      results: [
        buildRun({
          tags: [
            buildPipelineTag({
              key: DagsterTag.Partition,
              value: '5',
            }),
            buildPipelineTag({
              key: DagsterTag.Backfill,
              value: 'abc123',
            }),
            buildPipelineTag({
              key: DagsterTag.SensorName,
              value: 's3_sensor',
            }),
            buildPipelineTag({
              key: 'snowflake_db',
              value: 'customers',
            }),
            buildPipelineTag({
              key: 'team',
              value: 'sales',
            }),
            buildPipelineTag({
              key: 'job',
              value: 'cloud_analytics',
            }),
            buildPipelineTag({
              key: 'max_run_time',
              value: '2700',
            }),
            buildPipelineTag({
              key: 'automated',
              value: 'true',
            }),
          ],
        }),
        buildRun(),
        buildRun(),
        buildRun(),
        buildRun(),
        buildRun(),
        buildRun(),
      ],
    }),
  },
});
