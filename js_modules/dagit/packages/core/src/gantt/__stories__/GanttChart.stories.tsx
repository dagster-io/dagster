import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Box, Button, Colors, CustomTooltipProvider} from '@dagster-io/ui';
import {Meta} from '@storybook/react';
import React, {useState} from 'react';

import {RunStatus, buildRun, buildRunGroup, buildRunStatsSnapshot} from '../../graphql/types';
import {extractMetadataFromLogs} from '../../runs/RunMetadataProvider';
import {RunMetadataProviderMessageFragment} from '../../runs/types/RunMetadataProvider.types';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext';
import {IGanttNode} from '../Constants';
import {GanttChart, GanttChartLoadingState} from '../GanttChart';
import {RUN_GROUP_PANEL_QUERY} from '../RunGroupPanel';
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

const GRAPH: IGanttNode[] = [
  {name: 'A', inputs: [], outputs: [{dependedBy: [{solid: {name: 'B_very_long_step_name'}}]}]},
  {
    name: 'B_very_long_step_name',
    inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'C'}}, {solid: {name: 'D'}}]}],
  },
  {
    name: 'C',
    inputs: [{dependsOn: [{solid: {name: 'B_very_long_step_name'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'E'}}]}],
  },
  {
    name: 'D',
    inputs: [{dependsOn: [{solid: {name: 'B_very_long_step_name'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'E'}}]}],
  },
  {
    name: 'E',
    inputs: [{dependsOn: [{solid: {name: 'C'}}, {solid: {name: 'D'}}]}],
    outputs: [],
  },
];

const LOGS: RunMetadataProviderMessageFragment[] = [
  {
    message: '',
    timestamp: '0',
    stepKey: null,
    __typename: 'RunStartingEvent',
  },
  {
    message: 'Started process for pipeline (pid: 76720).',
    timestamp: '0',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: null,
    markerEnd: 'cli_api_subprocess_init',
  },
  {
    message: 'Started execution of pipeline "composition".',
    timestamp: '0',
    stepKey: null,
    __typename: 'RunStartEvent',
  },
  {
    message: 'Executing steps in process (pid: 76720)',
    timestamp: '0',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: null,
    markerEnd: null,
  },
  {
    message: 'Starting initialization of resources [io_manager].',
    timestamp: '0',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: 'resources',
    markerEnd: null,
  },
  {
    message: 'Finished initialization of resources [io_manager].',
    timestamp: '0',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: null,
    markerEnd: 'resources',
  },
  {
    message: 'Started execution of step "A".',
    timestamp: '0',
    stepKey: 'A',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message: 'Yielded output "result" of type "Int". (Type check passed).',
    timestamp: '0',
    stepKey: 'A',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '0',
    stepKey: 'A',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "A" in 82ms.',
    timestamp: '0',
    stepKey: 'A',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Started execution of step "B".',
    timestamp: '0',
    stepKey: 'B_very_long_step_name',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message: 'Got input "numbers" of type "[Int]". (Type check passed).',
    timestamp: '0',
    stepKey: 'B_very_long_step_name',
    __typename: 'ExecutionStepInputEvent',
  },
  {
    message: 'Execution of step "B" failed and has requested a retry in 2 seconds.',
    timestamp: '0',
    stepKey: 'B_very_long_step_name',
    __typename: 'ExecutionStepUpForRetryEvent',
  },
  {
    message: 'Started re-execution (attempt # 2) of step "retry_solid".',
    timestamp: '0',
    stepKey: 'B_very_long_step_name',
    __typename: 'ExecutionStepRestartEvent',
  },
  {
    message: 'Yielded output "result" of type "Any". (Type check passed).',
    timestamp: '0',
    stepKey: 'B_very_long_step_name',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '0',
    stepKey: 'B_very_long_step_name',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "B" in 33ms.',
    timestamp: '0',
    stepKey: 'B_very_long_step_name',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Starting initialization of resources [io_manager].',
    timestamp: '0',
    markerStart: `c-resource-1`,
    markerEnd: null,
    stepKey: 'C',
    __typename: 'ResourceInitStartedEvent',
  },
  {
    message: 'Finished initialization of resources [io_manager].',
    timestamp: '0',
    markerStart: null,
    markerEnd: `c-resource-1`,
    stepKey: 'C',
    __typename: 'ResourceInitSuccessEvent',
  },
  {
    message: 'Started execution of step "C".',
    timestamp: '0',
    stepKey: 'C',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message:
      'Loaded input "numbers" using input manager "io_manager", from output "result" of step "B"',
    timestamp: '0',
    stepKey: 'C',
    __typename: 'LoadedInputEvent',
  },
  {
    message:
      'Loaded input "numbers" using input manager "io_manager", from output "result" of step "B"',
    timestamp: '0',
    stepKey: 'C',
    __typename: 'LoadedInputEvent',
  },
  {
    message: 'Got input "numbers" of type "[Int]". (Type check passed).',
    timestamp: '0',
    stepKey: 'C',
    __typename: 'ExecutionStepInputEvent',
  },
  {
    message: 'Yielded output "result" of type "Int". (Type check passed).',
    timestamp: '0',
    stepKey: 'C',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '0',
    stepKey: 'C',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "C" in 34ms.',
    timestamp: '0',
    stepKey: 'C',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Started execution of step "D".',
    timestamp: '0',
    stepKey: 'D',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message:
      'Loaded input "numbers" using input manager "io_manager", from output "result" of step "B"',
    timestamp: '0',
    stepKey: 'D',
    __typename: 'LoadedInputEvent',
  },
  {
    message:
      'Loaded input "numbers" using input manager "io_manager", from output "result" of step "C"',
    timestamp: '0',
    stepKey: 'D',
    __typename: 'LoadedInputEvent',
  },
  {
    message: 'Got input "numbers" of type "[Int]". (Type check passed).',
    timestamp: '0',
    stepKey: 'D',
    __typename: 'ExecutionStepInputEvent',
  },
  {
    message: 'Yielded output "result" of type "Int". (Type check passed).',
    timestamp: '0',
    stepKey: 'D',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '0',
    stepKey: 'D',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "D" in 32ms.',
    timestamp: '0',
    stepKey: 'D',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Started execution of step "E".',
    timestamp: '0',
    stepKey: 'E',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message:
      'Loaded input "num" using input manager "io_manager", from output "result" of step "D"',
    timestamp: '0',
    stepKey: 'E',
    __typename: 'LoadedInputEvent',
  },
  {
    message: 'Got input "num" of type "Int". (Type check passed).',
    timestamp: '0',
    stepKey: 'E',
    __typename: 'ExecutionStepInputEvent',
  },
  {
    message: 'Yielded output "result" of type "Float". (Type check passed).',
    timestamp: '0',
    stepKey: 'E',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '0',
    stepKey: 'E',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "E" in 34ms.',
    timestamp: '0',
    stepKey: 'E',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Finished steps in process (pid: 76720) in 1.13s',
    timestamp: '0',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: null,
    markerEnd: null,
  },
  {
    message: 'Finished execution of pipeline "composition".',
    timestamp: '0',
    stepKey: null,
    __typename: 'RunSuccessEvent',
  },
  {
    message: 'Process for pipeline exited (pid: 76720).',
    timestamp: '0',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: null,
    markerEnd: null,
  },
];

LOGS.forEach((log, ii) => {
  log.timestamp = `${R2_START * 1000 + ii * 3000000}`;
});

// eslint-disable-next-line import/no-default-export
export default {
  title: 'GanttChart',
  component: GanttChart,
} as Meta;

export const InteractiveCase = (argValues: any) => {
  const [selectionQuery, setSelectionQuery] = useState<string>('');
  const [selectionKeys, setSelectionKeys] = useState<string[]>([]);
  const [progress, setProgress] = useState<number>(5);

  const metadata = extractMetadataFromLogs(LOGS.slice(0, progress));

  return (
    <MockedProvider mocks={[runGroupMock]}>
      <WorkspaceProvider>
        <CustomTooltipProvider />
        <Box
          flex={{gap: 8, alignItems: 'center'}}
          padding={8}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <Button onClick={() => setProgress(5)}>Reset</Button>
          <Button onClick={() => setProgress(Math.min(LOGS.length - 1, progress + 1))}>
            Send Next Log
          </Button>
          {`Log ${progress} / ${LOGS.length - 1}`}
        </Box>
        <div style={{width: '100%', height: 400}}>
          <GanttChart
            overrideNowTime={metadata.mostRecentLogAt}
            metadata={metadata}
            focusedTime={argValues.focusedTime}
            runId="r2"
            graph={GRAPH}
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
