import {buildQueryMock} from '../../assets/AutoMaterializePolicyPage/__fixtures__/AutoMaterializePolicyPage.fixtures';
import {buildRuns, buildRun, buildPipelineTag} from '../../graphql/types';
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
              value: 'five',
            }),
            buildPipelineTag({
              key: DagsterTag.Backfill,
              value: 'seven',
            }),
            buildPipelineTag({
              key: DagsterTag.SensorName,
              value: 'sensor',
            }),
            buildPipelineTag({
              key: 'Marco',
              value: 'Polo',
            }),
            buildPipelineTag({
              key: 'Test',
              value: 'Test2',
            }),
            buildPipelineTag({
              key: 'PinMe',
              value: 'Please',
            }),
            buildPipelineTag({
              key: 'context',
              value: 'contextValue',
            }),
            buildPipelineTag({
              key: 'Marco2',
              value: 'Polo2',
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
