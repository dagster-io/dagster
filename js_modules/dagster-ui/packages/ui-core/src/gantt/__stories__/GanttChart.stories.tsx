import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Box, Button, CustomTooltipProvider} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';
import {useState} from 'react';

import {GraphQueryItem} from '../../app/GraphQueryImpl';
import {RunStatus, buildRun, buildRunGroup, buildRunStatsSnapshot} from '../../graphql/types';
import {extractMetadataFromLogs} from '../../runs/RunMetadataProvider';
import {RunMetadataProviderMessageFragment} from '../../runs/types/RunMetadataProvider.types';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {GanttChart, GanttChartLoadingState} from '../GanttChart';
import {RUN_GROUP_PANEL_QUERY} from '../RunGroupPanel';
import * as Dynamic from '../__fixtures__/dynamic';
import * as Retry from '../__fixtures__/retry';
import * as Simple from '../__fixtures__/simple';
import {RunGroupPanelQuery, RunGroupPanelQueryVariables} from '../types/RunGroupPanel.types';

const R1_START = 1619468000;
const R2_START = 1619468000 + 30000;

const runGroupMock: MockedResponse<RunGroupPanelQuery, RunGroupPanelQueryVariables> = {
  request: {
    query: RUN_GROUP_PANEL_QUERY,
    variables: {runId: 'r2'},
  },
  result: {
    data: {
      __typename: 'Query',
      runGroupOrError: buildRunGroup({
        rootRunId: 'r1',
        runs: [
          buildRun({
            id: 'r1',
            runId: 'r1',
            parentRunId: null,
            status: RunStatus.FAILURE,
            stepKeysToExecute: [],
            pipelineName: 'Test',
            tags: [],
            stats: buildRunStatsSnapshot({
              id: 'r1',
              enqueuedTime: R1_START,
              launchTime: R1_START + 12,
              startTime: R1_START + 24,
              endTime: R1_START + 400,
            }),
          }),
          buildRun({
            id: 'r2',
            runId: 'r2',
            parentRunId: 'r1',
            status: RunStatus.STARTING,
            stepKeysToExecute: [],
            pipelineName: 'Test',
            tags: [],
            stats: buildRunStatsSnapshot({
              id: 'r2',
              enqueuedTime: R2_START,
              launchTime: R2_START + 12,
              startTime: null,
              endTime: null,
            }),
          }),
        ],
      }),
    },
  },
};

const GanttTestCase = ({
  graph,
  logs,
  focusedTime,
}: {
  graph: GraphQueryItem[];
  logs: RunMetadataProviderMessageFragment[];
  focusedTime: number;
}) => {
  const [selectionQuery, setSelectionQuery] = useState<string>('');
  const [selectionKeys, setSelectionKeys] = useState<string[]>([]);
  const [progress, setProgress] = useState<number>(5);

  const metadata = extractMetadataFromLogs(logs.slice(0, progress));

  logs.forEach((log, ii) => {
    log.timestamp = `${R2_START * 1000 + ii * 3000000}`;
  });

  return (
    <MockedProvider mocks={[runGroupMock]}>
      <WorkspaceProvider>
        <CustomTooltipProvider />
        <Box flex={{gap: 8, alignItems: 'center'}} padding={8} border="bottom">
          <Button onClick={() => setProgress(5)}>Reset</Button>
          <Button onClick={() => setProgress(Math.min(logs.length - 1, progress + 1))}>
            Send Next Log
          </Button>
          <Button onClick={() => setProgress(logs.length - 1)}>Send All Logs</Button>
          {`Log ${progress} / ${logs.length - 1}`}
        </Box>
        <div style={{width: '100%', height: 400}}>
          <GanttChart
            overrideNowTime={metadata.mostRecentLogAt}
            metadata={metadata}
            focusedTime={focusedTime}
            runId="r2"
            graph={graph}
            selection={{query: selectionQuery, keys: selectionKeys}}
            onClickStep={(step) => {
              setSelectionKeys([step]);
              setSelectionQuery([step].join(', ') || '*');
            }}
            onSetSelection={setSelectionQuery}
          />
        </div>
      </WorkspaceProvider>
    </MockedProvider>
  );
};

// eslint-disable-next-line import/no-default-export
export default {
  title: 'GanttChart',
  component: GanttChart,
} as Meta;

export const SimpleCase = (argValues: any) => {
  return (
    <GanttTestCase graph={Simple.GRAPH} logs={Simple.LOGS} focusedTime={argValues.focusedTime} />
  );
};

export const RetryCase = (argValues: any) => {
  return (
    <GanttTestCase graph={Retry.GRAPH} logs={Retry.LOGS} focusedTime={argValues.focusedTime} />
  );
};

export const DynamicCase = (argValues: any) => {
  return (
    <GanttTestCase graph={Dynamic.GRAPH} logs={Dynamic.LOGS} focusedTime={argValues.focusedTime} />
  );
};

export const EmptyStateCase = () => {
  return (
    <MockedProvider mocks={[runGroupMock]}>
      <WorkspaceProvider>
        <CustomTooltipProvider />
        <div style={{width: '100%', height: 400}}>
          <GanttChartLoadingState runId="r2" />
        </div>
      </WorkspaceProvider>
    </MockedProvider>
  );
};
