import {RunMetadataProviderMessageFragment} from '../../runs/types/RunMetadataProvider.types';
import {IGanttNode} from '../Constants';

export const GRAPH: IGanttNode[] = [
  {
    name: 'load_pieces',
    inputs: [],
    outputs: [
      {
        dependedBy: [
          {solid: {name: 'compute_piece[1_XASD_plus_8]'}},
          {solid: {name: 'compute_piece[2_XASD_plus_8]'}},
          {solid: {name: 'compute_piece[3_XASD_plus_8]'}},
          {solid: {name: 'compute_piece[4_XASD_plus_8]'}},
          {solid: {name: 'compute_piece[?]'}},
        ],
      },
    ],
  },
  {
    name: 'compute_piece[1_XASD_plus_8]',
    inputs: [{dependsOn: [{solid: {name: 'load_pieces'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'merge_and_analyze'}}]}],
  },
  {
    name: 'compute_piece[2_XASD_plus_8]',
    inputs: [{dependsOn: [{solid: {name: 'load_pieces'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'merge_and_analyze'}}]}],
  },
  {
    name: 'compute_piece[3_XASD_plus_8]',
    inputs: [{dependsOn: [{solid: {name: 'load_pieces'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'merge_and_analyze'}}]}],
  },
  {
    name: 'compute_piece[4_XASD_plus_8]',
    inputs: [{dependsOn: [{solid: {name: 'load_pieces'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'merge_and_analyze'}}]}],
  },
  {
    name: 'compute_piece[?]',
    inputs: [{dependsOn: [{solid: {name: 'load_pieces'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'merge_and_analyze'}}]}],
  },
  {
    name: 'merge_and_analyze',
    inputs: [
      {
        dependsOn: [
          {solid: {name: 'compute_piece[1_XASD_plus_8]'}},
          {solid: {name: 'compute_piece[2_XASD_plus_8]'}},
          {solid: {name: 'compute_piece[3_XASD_plus_8]'}},
          {solid: {name: 'compute_piece[4_XASD_plus_8]'}},
          {solid: {name: 'compute_piece[?]'}},
        ],
      },
    ],
    outputs: [],
  },
];

export const LOGS: RunMetadataProviderMessageFragment[] = [
  {
    message: '',
    timestamp: '1690127338218',
    stepKey: null,
    __typename: 'RunStartingEvent',
  },
  {
    message: 'Started process for run (pid: 66177).',
    timestamp: '1690127339000',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: null,
    markerEnd: null,
  },
  {
    message: 'Started execution of run for "dynamic_graph".',
    timestamp: '1690127339178',
    stepKey: null,
    __typename: 'RunStartEvent',
  },
  {
    message: 'Executing steps using multiprocess executor: parent process (pid: 66177)',
    timestamp: '1690127339227',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: null,
    markerEnd: null,
  },
  {
    message: 'Launching subprocess for "load_pieces".',
    timestamp: '1690127339235',
    stepKey: 'load_pieces',
    __typename: 'StepWorkerStartingEvent',
    markerStart: 'step_process_start',
    markerEnd: null,
  },
  {
    message: 'Executing step "load_pieces" in subprocess.',
    timestamp: '1690127339899',
    stepKey: 'load_pieces',
    __typename: 'StepWorkerStartedEvent',
    markerStart: null,
    markerEnd: 'step_process_start',
  },
  {
    message: 'Starting initialization of resources [io_manager].',
    timestamp: '1690127339924',
    stepKey: 'load_pieces',
    __typename: 'ResourceInitStartedEvent',
    markerStart: 'resources',
    markerEnd: null,
  },
  {
    message: 'Finished initialization of resources [io_manager].',
    timestamp: '1690127339945',
    stepKey: 'load_pieces',
    __typename: 'ResourceInitSuccessEvent',
    markerStart: null,
    markerEnd: 'resources',
  },
  {
    message: 'Started execution of step "load_pieces".',
    timestamp: '1690127339988',
    stepKey: 'load_pieces',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message:
      'Yielded output "result" mapping key "1_XASD_plus_8" of type "Any". (Type check passed).',
    timestamp: '1690127340007',
    stepKey: 'load_pieces',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message:
      'Writing file at: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/load_pieces/result/1_XASD_plus_8 using PickledObjectFilesystemIOManager...',
    timestamp: '1690127340017',
    stepKey: 'load_pieces',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '1690127340026',
    stepKey: 'load_pieces',
    __typename: 'HandledOutputEvent',
  },
  {
    message:
      'Yielded output "result" mapping key "2_XASD_plus_8" of type "Any". (Type check passed).',
    timestamp: '1690127341036',
    stepKey: 'load_pieces',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message:
      'Writing file at: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/load_pieces/result/2_XASD_plus_8 using PickledObjectFilesystemIOManager...',
    timestamp: '1690127341068',
    stepKey: 'load_pieces',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '1690127341093',
    stepKey: 'load_pieces',
    __typename: 'HandledOutputEvent',
  },
  {
    message:
      'Yielded output "result" mapping key "3_XASD_plus_8" of type "Any". (Type check passed).',
    timestamp: '1690127342113',
    stepKey: 'load_pieces',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message:
      'Writing file at: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/load_pieces/result/3_XASD_plus_8 using PickledObjectFilesystemIOManager...',
    timestamp: '1690127342142',
    stepKey: 'load_pieces',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '1690127342159',
    stepKey: 'load_pieces',
    __typename: 'HandledOutputEvent',
  },
  {
    message:
      'Yielded output "result" mapping key "4_XASD_plus_8" of type "Any". (Type check passed).',
    timestamp: '1690127343184',
    stepKey: 'load_pieces',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message:
      'Writing file at: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/load_pieces/result/4_XASD_plus_8 using PickledObjectFilesystemIOManager...',
    timestamp: '1690127343209',
    stepKey: 'load_pieces',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '1690127343242',
    stepKey: 'load_pieces',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "load_pieces" in 4.25s.',
    timestamp: '1690127344260',
    stepKey: 'load_pieces',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Launching subprocess for "compute_piece[1_XASD_plus_8]".',
    timestamp: '1690127344421',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'StepWorkerStartingEvent',
    markerStart: 'step_process_start',
    markerEnd: null,
  },
  {
    message: 'Launching subprocess for "compute_piece[2_XASD_plus_8]".',
    timestamp: '1690127344449',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'StepWorkerStartingEvent',
    markerStart: 'step_process_start',
    markerEnd: null,
  },
  {
    message: 'Launching subprocess for "compute_piece[3_XASD_plus_8]".',
    timestamp: '1690127344467',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'StepWorkerStartingEvent',
    markerStart: 'step_process_start',
    markerEnd: null,
  },
  {
    message: 'Launching subprocess for "compute_piece[4_XASD_plus_8]".',
    timestamp: '1690127344475',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'StepWorkerStartingEvent',
    markerStart: 'step_process_start',
    markerEnd: null,
  },
  {
    message: 'Executing step "compute_piece[1_XASD_plus_8]" in subprocess.',
    timestamp: '1690127345193',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'StepWorkerStartedEvent',
    markerStart: null,
    markerEnd: 'step_process_start',
  },
  {
    message: 'Executing step "compute_piece[2_XASD_plus_8]" in subprocess.',
    timestamp: '1690127345201',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'StepWorkerStartedEvent',
    markerStart: null,
    markerEnd: 'step_process_start',
  },
  {
    message: 'Starting initialization of resources [io_manager].',
    timestamp: '1690127345203',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'ResourceInitStartedEvent',
    markerStart: 'resources',
    markerEnd: null,
  },
  {
    message: 'Finished initialization of resources [io_manager].',
    timestamp: '1690127345212',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'ResourceInitSuccessEvent',
    markerStart: null,
    markerEnd: 'resources',
  },
  {
    message: 'Starting initialization of resources [io_manager].',
    timestamp: '1690127345212',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'ResourceInitStartedEvent',
    markerStart: 'resources',
    markerEnd: null,
  },
  {
    message: 'Executing step "compute_piece[3_XASD_plus_8]" in subprocess.',
    timestamp: '1690127345220',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'StepWorkerStartedEvent',
    markerStart: null,
    markerEnd: 'step_process_start',
  },
  {
    message: 'Finished initialization of resources [io_manager].',
    timestamp: '1690127345223',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'ResourceInitSuccessEvent',
    markerStart: null,
    markerEnd: 'resources',
  },
  {
    message: 'Starting initialization of resources [io_manager].',
    timestamp: '1690127345235',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'ResourceInitStartedEvent',
    markerStart: 'resources',
    markerEnd: null,
  },
  {
    message: 'Finished initialization of resources [io_manager].',
    timestamp: '1690127345248',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'ResourceInitSuccessEvent',
    markerStart: null,
    markerEnd: 'resources',
  },
  {
    message: 'Executing step "compute_piece[4_XASD_plus_8]" in subprocess.',
    timestamp: '1690127345249',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'StepWorkerStartedEvent',
    markerStart: null,
    markerEnd: 'step_process_start',
  },
  {
    message: 'Started execution of step "compute_piece[1_XASD_plus_8]".',
    timestamp: '1690127345249',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message: 'Starting initialization of resources [io_manager].',
    timestamp: '1690127345263',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'ResourceInitStartedEvent',
    markerStart: 'resources',
    markerEnd: null,
  },
  {
    message:
      'Loading file from: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/load_pieces/result/1_XASD_plus_8 using PickledObjectFilesystemIOManager...',
    timestamp: '1690127345264',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Started execution of step "compute_piece[2_XASD_plus_8]".',
    timestamp: '1690127345267',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message: 'Finished initialization of resources [io_manager].',
    timestamp: '1690127345276',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'ResourceInitSuccessEvent',
    markerStart: null,
    markerEnd: 'resources',
  },
  {
    message:
      'Loaded input "piece" using input manager "io_manager", from output "result" of step "load_pieces"',
    timestamp: '1690127345276',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'LoadedInputEvent',
  },
  {
    message:
      'Loading file from: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/load_pieces/result/2_XASD_plus_8 using PickledObjectFilesystemIOManager...',
    timestamp: '1690127345279',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Got input "piece" of type "Any". (Type check passed).',
    timestamp: '1690127345288',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'ExecutionStepInputEvent',
  },
  {
    message:
      'Loaded input "piece" using input manager "io_manager", from output "result" of step "load_pieces"',
    timestamp: '1690127345290',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'LoadedInputEvent',
  },
  {
    message: 'Started execution of step "compute_piece[3_XASD_plus_8]".',
    timestamp: '1690127345302',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message: 'Got input "piece" of type "Any". (Type check passed).',
    timestamp: '1690127345304',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'ExecutionStepInputEvent',
  },
  {
    message:
      'Loading file from: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/load_pieces/result/3_XASD_plus_8 using PickledObjectFilesystemIOManager...',
    timestamp: '1690127345320',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Started execution of step "compute_piece[4_XASD_plus_8]".',
    timestamp: '1690127345323',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message:
      'Loaded input "piece" using input manager "io_manager", from output "result" of step "load_pieces"',
    timestamp: '1690127345332',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'LoadedInputEvent',
  },
  {
    message:
      'Loading file from: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/load_pieces/result/4_XASD_plus_8 using PickledObjectFilesystemIOManager...',
    timestamp: '1690127345334',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Got input "piece" of type "Any". (Type check passed).',
    timestamp: '1690127345344',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'ExecutionStepInputEvent',
  },
  {
    message:
      'Loaded input "piece" using input manager "io_manager", from output "result" of step "load_pieces"',
    timestamp: '1690127345345',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'LoadedInputEvent',
  },
  {
    message: 'Got input "piece" of type "Any". (Type check passed).',
    timestamp: '1690127345357',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'ExecutionStepInputEvent',
  },
  {
    message: 'Yielded output "result" of type "Any". (Type check passed).',
    timestamp: '1690127353305',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message:
      'Writing file at: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/compute_piece[1_XASD_plus_8]/result using PickledObjectFilesystemIOManager...',
    timestamp: '1690127353340',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '1690127353395',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "compute_piece[1_XASD_plus_8]" in 8.11s.',
    timestamp: '1690127353411',
    stepKey: 'compute_piece[1_XASD_plus_8]',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Yielded output "result" of type "Any". (Type check passed).',
    timestamp: '1690127361330',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message:
      'Writing file at: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/compute_piece[2_XASD_plus_8]/result using PickledObjectFilesystemIOManager...',
    timestamp: '1690127361375',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '1690127361399',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "compute_piece[2_XASD_plus_8]" in 16.09s.',
    timestamp: '1690127361415',
    stepKey: 'compute_piece[2_XASD_plus_8]',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Yielded output "result" of type "Any". (Type check passed).',
    timestamp: '1690127369368',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message:
      'Writing file at: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/compute_piece[3_XASD_plus_8]/result using PickledObjectFilesystemIOManager...',
    timestamp: '1690127369402',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '1690127369426',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "compute_piece[3_XASD_plus_8]" in 24.1s.',
    timestamp: '1690127369456',
    stepKey: 'compute_piece[3_XASD_plus_8]',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Yielded output "result" of type "Any". (Type check passed).',
    timestamp: '1690127377385',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message:
      'Writing file at: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/compute_piece[4_XASD_plus_8]/result using PickledObjectFilesystemIOManager...',
    timestamp: '1690127377433',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '1690127377461',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "compute_piece[4_XASD_plus_8]" in 32.11s.',
    timestamp: '1690127377484',
    stepKey: 'compute_piece[4_XASD_plus_8]',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Launching subprocess for "merge_and_analyze".',
    timestamp: '1690127377621',
    stepKey: 'merge_and_analyze',
    __typename: 'StepWorkerStartingEvent',
    markerStart: 'step_process_start',
    markerEnd: null,
  },
  {
    message: 'Executing step "merge_and_analyze" in subprocess.',
    timestamp: '1690127378309',
    stepKey: 'merge_and_analyze',
    __typename: 'StepWorkerStartedEvent',
    markerStart: null,
    markerEnd: 'step_process_start',
  },
  {
    message: 'Starting initialization of resources [io_manager].',
    timestamp: '1690127378336',
    stepKey: 'merge_and_analyze',
    __typename: 'ResourceInitStartedEvent',
    markerStart: 'resources',
    markerEnd: null,
  },
  {
    message: 'Finished initialization of resources [io_manager].',
    timestamp: '1690127378362',
    stepKey: 'merge_and_analyze',
    __typename: 'ResourceInitSuccessEvent',
    markerStart: null,
    markerEnd: 'resources',
  },
  {
    message: 'Started execution of step "merge_and_analyze".',
    timestamp: '1690127378396',
    stepKey: 'merge_and_analyze',
    __typename: 'ExecutionStepStartEvent',
  },
  {
    message:
      'Loading file from: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/compute_piece[1_XASD_plus_8]/result using PickledObjectFilesystemIOManager...',
    timestamp: '1690127378406',
    stepKey: 'merge_and_analyze',
    __typename: 'LogMessageEvent',
  },
  {
    message:
      'Loaded input "pieces" using input manager "io_manager", from output "result" of step "compute_piece[1_XASD_plus_8]"',
    timestamp: '1690127378414',
    stepKey: 'merge_and_analyze',
    __typename: 'LoadedInputEvent',
  },
  {
    message:
      'Loading file from: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/compute_piece[2_XASD_plus_8]/result using PickledObjectFilesystemIOManager...',
    timestamp: '1690127378423',
    stepKey: 'merge_and_analyze',
    __typename: 'LogMessageEvent',
  },
  {
    message:
      'Loaded input "pieces" using input manager "io_manager", from output "result" of step "compute_piece[2_XASD_plus_8]"',
    timestamp: '1690127378432',
    stepKey: 'merge_and_analyze',
    __typename: 'LoadedInputEvent',
  },
  {
    message:
      'Loading file from: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/compute_piece[3_XASD_plus_8]/result using PickledObjectFilesystemIOManager...',
    timestamp: '1690127378441',
    stepKey: 'merge_and_analyze',
    __typename: 'LogMessageEvent',
  },
  {
    message:
      'Loaded input "pieces" using input manager "io_manager", from output "result" of step "compute_piece[3_XASD_plus_8]"',
    timestamp: '1690127378450',
    stepKey: 'merge_and_analyze',
    __typename: 'LoadedInputEvent',
  },
  {
    message:
      'Loading file from: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/compute_piece[4_XASD_plus_8]/result using PickledObjectFilesystemIOManager...',
    timestamp: '1690127378458',
    stepKey: 'merge_and_analyze',
    __typename: 'LogMessageEvent',
  },
  {
    message:
      'Loaded input "pieces" using input manager "io_manager", from output "result" of step "compute_piece[4_XASD_plus_8]"',
    timestamp: '1690127378466',
    stepKey: 'merge_and_analyze',
    __typename: 'LoadedInputEvent',
  },
  {
    message: 'Got input "pieces" of type "Any". (Type check passed).',
    timestamp: '1690127378474',
    stepKey: 'merge_and_analyze',
    __typename: 'ExecutionStepInputEvent',
  },
  {
    message: 'Yielded output "result" of type "Any". (Type check passed).',
    timestamp: '1690127378483',
    stepKey: 'merge_and_analyze',
    __typename: 'ExecutionStepOutputEvent',
  },
  {
    message:
      'Writing file at: /Users/bengotow/dagster-home/storage/storage/3e061a7b-a7ec-4adc-bafc-8608ca2ea56c/merge_and_analyze/result using PickledObjectFilesystemIOManager...',
    timestamp: '1690127378492',
    stepKey: 'merge_and_analyze',
    __typename: 'LogMessageEvent',
  },
  {
    message: 'Handled output "result" using IO manager "io_manager"',
    timestamp: '1690127378501',
    stepKey: 'merge_and_analyze',
    __typename: 'HandledOutputEvent',
  },
  {
    message: 'Finished execution of step "merge_and_analyze" in 25ms.',
    timestamp: '1690127378509',
    stepKey: 'merge_and_analyze',
    __typename: 'ExecutionStepSuccessEvent',
  },
  {
    message: 'Multiprocess executor: parent process exiting after 39.43s (pid: 66177)',
    timestamp: '1690127378668',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: null,
    markerEnd: null,
  },
  {
    message: 'Finished execution of run for "dynamic_graph".',
    timestamp: '1690127378687',
    stepKey: null,
    __typename: 'RunSuccessEvent',
  },
  {
    message: 'Process for run exited (pid: 66177).',
    timestamp: '1690127378734',
    stepKey: null,
    __typename: 'EngineEvent',
    markerStart: null,
    markerEnd: null,
  },
];
