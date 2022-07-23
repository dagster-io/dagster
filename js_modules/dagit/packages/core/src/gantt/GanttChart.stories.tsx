import {CustomTooltipProvider} from '@dagster-io/ui';
import {Meta} from '@storybook/react/types-6-0';
import React, {useState} from 'react';

import {extractMetadataFromLogs} from '../runs/RunMetadataProvider';
import {RunMetadataProviderMessageFragment} from '../runs/types/RunMetadataProviderMessageFragment';
import {StorybookProvider} from '../testing/StorybookProvider';
import {RunStatus} from '../types/globalTypes';

import {IGanttNode} from './Constants';
import {GanttChart, GanttChartLoadingState} from './GanttChart';

const R1_START = 1619468000;
const R2_START = 1619468000 + 30000;

const APOLLO_MOCKS = {
  RunGroupOrError: () => ({
    __typename: 'RunGroup',
    rootRunId: 'r1',
    runs: [
      {
        __typename: 'Run',
        id: 'r1',
        runId: 'r1',
        parentRunId: null,
        status: RunStatus.FAILURE,
        stepKeysToExecute: [],
        pipelineName: 'Test',
        tags: [],
        stats: {
          __typename: 'RunStatsSnapshot',
          id: 'r1',
          enqueuedTime: R1_START,
          launchTime: R1_START + 12,
          startTime: R1_START + 24,
          endTime: R1_START + 400,
        },
      },
      {
        __typename: 'Run',
        id: 'r2',
        runId: 'r2',
        parentRunId: 'r1',
        status: RunStatus.STARTING,
        stepKeysToExecute: [],
        pipelineName: 'Test',
        tags: [],
        stats: {
          __typename: 'RunStatsSnapshot',
          id: 'r2',
          enqueuedTime: R2_START,
          launchTime: R2_START + 12,
          startTime: null,
          endTime: null,
        },
      },
    ],
  }),
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

for (let ii = 0; ii < LOGS.length; ii++) {
  LOGS[ii].timestamp = `${R2_START + ii * 100}`;
}

// eslint-disable-next-line import/no-default-export
export default {
  title: 'GanttChart',
  component: GanttChart,
  argTypes: {
    progress: {
      defaultValue: 0,
      control: {
        type: 'range',
        min: 0,
        max: LOGS.length,
        step: 1,
      },
    },
    focusedTime: {
      control: {
        type: 'range',
        min: Number(LOGS[0].timestamp),
        max: Number(LOGS[LOGS.length - 1].timestamp),
        step: 1,
      },
    },
    metadata: {control: {disable: true}},
    runId: {control: {disable: true}},
    graph: {control: {disable: true}},
    selection: {control: {disable: true}},
    toolbarActions: {control: {disable: true}},
  },
} as Meta;

export const EmptyStateCase = () => {
  return (
    <StorybookProvider apolloProps={{mocks: APOLLO_MOCKS}}>
      <CustomTooltipProvider />
      <div style={{width: '100%', height: 400}}>
        <GanttChartLoadingState runId="r2" />
      </div>
    </StorybookProvider>
  );
};

export const InteractiveCase = (argValues: any) => {
  const [selectionQuery, setSelectionQuery] = useState<string>('');
  const [selectionKeys, setSelectionKeys] = useState<string[]>([]);

  const metadata = extractMetadataFromLogs(LOGS.slice(0, argValues.progress));
  return (
    <StorybookProvider apolloProps={{mocks: APOLLO_MOCKS}}>
      <CustomTooltipProvider />
      <div style={{width: '100%', height: 400}}>
        <GanttChart
          key={metadata.mostRecentLogAt}
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
    </StorybookProvider>
  );
};
