import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import moment from 'moment';
import * as React from 'react';

import {StorybookProvider} from '../testing/StorybookProvider';
import {StepEventStatus} from '../types/globalTypes';
import {TokenizingFieldValue} from '../ui/TokenizingField';

import {PartitionRunMatrix} from './PartitionRunMatrix';
import {
  PartitionRunMatrixRunFragment,
  PartitionRunMatrixRunFragment_tags,
} from './types/PartitionRunMatrixRunFragment';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'PartitionRunMatrix',
  component: PartitionRunMatrix,
} as Meta;

interface ISolidHandle {
  __typename: 'SolidHandle';
  handleID: string;
  solid: {
    name: string;
    definition: {__typename: 'SolidDefinition'; name: string};
    inputs: {dependsOn: {solid: {name: string}}[]}[];
    outputs: {dependedBy: {solid: {name: string}}[]}[];
  };
}

// On the real PartitionView, the tags in the filter bar are passed as a GraphQL query param,
// to make them work just filter our sample data.
function simulateTagFilteringInQuery(
  runs: PartitionRunMatrixRunFragment[],
  runTags: TokenizingFieldValue[],
) {
  return runs.filter((r) =>
    runTags.every((t) => r.tags.some((rt) => `${rt.key}=${rt.value}` === t.value)),
  );
}

function buildSolidHandles(solidNames: string[], deps: string[]) {
  const result: ISolidHandle[] = [];
  for (const name of solidNames) {
    result.push({
      __typename: 'SolidHandle',
      handleID: name,
      solid: {
        name: name,
        definition: {
          __typename: 'SolidDefinition',
          name: name,
        },
        inputs: [],
        outputs: [],
      },
    });
  }
  for (const dep of deps) {
    const [_, from, to] = /([^\s]*)\s*=>\s*([^\s]*)/.exec(dep)!;
    result
      .find((s) => s.handleID === from)!
      .solid.outputs.push({
        dependedBy: [{solid: {name: to}}],
      });
    result
      .find((s) => s.handleID === to)!
      .solid.inputs.push({
        dependsOn: [{solid: {name: from}}],
      });
  }
  return result;
}

function buildRun(
  isoDateString: string,
  statuses: {[stepKey: string]: StepEventStatus},
  tags: PartitionRunMatrixRunFragment_tags[] = [],
) {
  const id = faker.random.uuid().slice(0, 8);
  const startTime = new Date(isoDateString).getTime() / 1000;
  const result: PartitionRunMatrixRunFragment = {
    __typename: 'PipelineRun',
    id: id,
    runId: id,
    stats: {
      id: id,
      startTime,
      __typename: 'PipelineRunStatsSnapshot',
    },
    stepStats: Object.entries(statuses).map(([key, status]) => ({
      __typename: 'PipelineRunStepStats',
      stepKey: key,
      status: status,
      materializations: [],
      expectationResults: [],
    })),
    tags: tags,
  };

  return result;
}

const PipelineMocks = {
  PipelineSnapshotOrError: () => ({
    __typename: 'PipelineSnapshot',
  }),
  PipelineSnapshot: () => ({
    name: () => 'TestPipeline',
    solidHandles: () =>
      buildSolidHandles(
        ['first', 'second', 'third', 'fourth'],
        ['first => second', 'first => third', 'second => fourth', 'third => fourth'],
      ),
  }),
};

export const BasicTestCases = () => {
  const [runTags, setRunTags] = React.useState<TokenizingFieldValue[]>([]);
  const [stepQuery, setStepQuery] = React.useState('');
  const partitions: {name: string; runs: PartitionRunMatrixRunFragment[]}[] = [];

  // Good Run
  partitions.push({
    name: '2021-01-01',
    runs: [
      buildRun('2021-01-01T00:00:00', {
        first: StepEventStatus.SUCCESS,
        second: StepEventStatus.SUCCESS,
        third: StepEventStatus.SUCCESS,
        fourth: StepEventStatus.SUCCESS,
      }),
    ],
  });
  // Partial Failure Run
  partitions.push({
    name: '2021-01-02',
    runs: [
      buildRun('2021-01-02T00:00:00', {
        first: StepEventStatus.SUCCESS,
        second: StepEventStatus.FAILURE,
        third: StepEventStatus.SUCCESS,
        fourth: StepEventStatus.SKIPPED,
      }),
    ],
  });
  // Some Steps Skipped Run
  partitions.push({
    name: '2021-01-03',
    runs: [
      buildRun('2021-01-03T00:00:00', {
        first: StepEventStatus.SUCCESS,
        second: StepEventStatus.SUCCESS,
        third: StepEventStatus.SKIPPED,
        fourth: StepEventStatus.SKIPPED,
      }),
    ],
  });
  // Still Running Run
  partitions.push({
    name: '2021-01-04',
    runs: [
      buildRun('2021-01-04T00:00:00', {
        first: StepEventStatus.SUCCESS,
      }),
    ],
  });

  // Day with No Runs
  partitions.push({
    name: '2021-01-05',
    runs: [],
  });

  // Partial Failure Run followed by "Restart from Failure" Run
  partitions.push({
    name: '2021-01-06',
    runs: [
      buildRun('2021-01-06T00:00:00', {
        first: StepEventStatus.SUCCESS,
        second: StepEventStatus.FAILURE,
        third: StepEventStatus.SKIPPED,
      }),
      buildRun(
        '2021-01-06T12:00:00',
        {
          second: StepEventStatus.SUCCESS,
          third: StepEventStatus.SUCCESS,
          fourth: StepEventStatus.SUCCESS,
        },
        [{__typename: 'PipelineTag', key: 'dagster/backfill', value: '1234'}],
      ),
    ],
  });

  // Successful run followed by a run with failure and skips
  partitions.push({
    name: '2021-01-07',
    runs: [
      buildRun('2021-01-07T00:00:00', {
        first: StepEventStatus.SUCCESS,
        second: StepEventStatus.SUCCESS,
        third: StepEventStatus.SUCCESS,
        fourth: StepEventStatus.SUCCESS,
      }),
      buildRun(
        '2021-01-07T12:00:00',
        {
          first: StepEventStatus.SUCCESS,
          second: StepEventStatus.FAILURE,
          third: StepEventStatus.SKIPPED,
        },
        [
          {__typename: 'PipelineTag', key: 'dagster/backfill', value: '1234'},
          {__typename: 'PipelineTag', key: 'randomtag', value: 'helloworld'},
        ],
      ),
    ],
  });

  return (
    <StorybookProvider apolloProps={{mocks: PipelineMocks}}>
      <PartitionRunMatrix
        pipelineName="TestPipeline"
        repoAddress={{name: 'Test', location: 'TestLocation'}}
        runTags={runTags}
        setRunTags={setRunTags}
        stepQuery={stepQuery}
        setStepQuery={setStepQuery}
        partitions={partitions.map((p) => ({
          ...p,
          runs: simulateTagFilteringInQuery(p.runs, runTags),
        }))}
      />
    </StorybookProvider>
  );
};

export const LargeDataset = () => {
  const [runTags, setRunTags] = React.useState<TokenizingFieldValue[]>([]);
  const [stepQuery, setStepQuery] = React.useState('');
  const partitions = React.useMemo(() => {
    const results: {name: string; runs: PartitionRunMatrixRunFragment[]}[] = [];
    for (let ii = 0; ii < 300; ii++) {
      const date = moment().startOf('year').add(ii, 'days');
      const runCount = faker.random.number(10);

      const runs: PartitionRunMatrixRunFragment[] = [];
      for (let x = 0; x < runCount; x++) {
        runs.push(
          buildRun(date.clone().add(x, 'minutes').toISOString(), {
            first: faker.random.objectElement(StepEventStatus) as any,
            second: faker.random.objectElement(StepEventStatus) as any,
            third: faker.random.objectElement(StepEventStatus) as any,
            fourth: faker.random.objectElement(StepEventStatus) as any,
          }),
        );
      }
      results.push({
        name: date.format('YYYY-MM-DD'),
        runs: runs,
      });
    }
    return results;
  }, []);

  return (
    <StorybookProvider apolloProps={{mocks: PipelineMocks}}>
      <PartitionRunMatrix
        pipelineName="TestPipeline"
        repoAddress={{name: 'Test', location: 'TestLocation'}}
        runTags={runTags}
        setRunTags={setRunTags}
        stepQuery={stepQuery}
        setStepQuery={setStepQuery}
        partitions={partitions.map((p) => ({
          ...p,
          runs: simulateTagFilteringInQuery(p.runs, runTags),
        }))}
      />
    </StorybookProvider>
  );
};
