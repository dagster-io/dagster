// Generated GraphQL types, do not edit manually.

export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & {[SubKey in K]?: Maybe<T[SubKey]>};
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & {[SubKey in K]: Maybe<T[SubKey]>};
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: string;
  String: string;
  Boolean: boolean;
  Int: number;
  Float: number;
  Cursor: any;
  GenericScalar: any;
  RunConfigData: any;
};

export type AddDynamicPartitionResult =
  | AddDynamicPartitionSuccess
  | DuplicateDynamicPartitionError
  | PythonError
  | UnauthorizedError;

export type AddDynamicPartitionSuccess = {
  __typename: 'AddDynamicPartitionSuccess';
  partitionKey: Scalars['String'];
  partitionsDefName: Scalars['String'];
};

export type AlertFailureEvent = MessageEvent &
  RunEvent & {
    __typename: 'AlertFailureEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type AlertStartEvent = MessageEvent &
  RunEvent & {
    __typename: 'AlertStartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type AlertSuccessEvent = MessageEvent &
  RunEvent & {
    __typename: 'AlertSuccessEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ArrayConfigType = ConfigType &
  WrappingConfigType & {
    __typename: 'ArrayConfigType';
    description: Maybe<Scalars['String']>;
    isSelector: Scalars['Boolean'];
    key: Scalars['String'];
    ofType: ConfigType;
    recursiveConfigTypes: Array<ConfigType>;
    typeParamKeys: Array<Scalars['String']>;
  };

export type Asset = {
  __typename: 'Asset';
  assetMaterializations: Array<MaterializationEvent>;
  assetObservations: Array<ObservationEvent>;
  definition: Maybe<AssetNode>;
  id: Scalars['String'];
  key: AssetKey;
};

export type AssetAssetMaterializationsArgs = {
  afterTimestampMillis?: InputMaybe<Scalars['String']>;
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitionInLast?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
  tags?: InputMaybe<Array<InputTag>>;
};

export type AssetAssetObservationsArgs = {
  afterTimestampMillis?: InputMaybe<Scalars['String']>;
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitionInLast?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
};

export type AssetConnection = {
  __typename: 'AssetConnection';
  nodes: Array<Asset>;
};

export type AssetDependency = {
  __typename: 'AssetDependency';
  asset: AssetNode;
  inputName: Scalars['String'];
};

export type AssetFreshnessInfo = {
  __typename: 'AssetFreshnessInfo';
  currentMinutesLate: Maybe<Scalars['Float']>;
  latestMaterializationMinutesLate: Maybe<Scalars['Float']>;
};

export type AssetGroup = {
  __typename: 'AssetGroup';
  assetKeys: Array<AssetKey>;
  groupName: Scalars['String'];
};

export type AssetGroupSelector = {
  groupName: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type AssetKey = {
  __typename: 'AssetKey';
  path: Array<Scalars['String']>;
};

export type AssetKeyInput = {
  path: Array<Scalars['String']>;
};

export type AssetLatestInfo = {
  __typename: 'AssetLatestInfo';
  assetKey: AssetKey;
  inProgressRunIds: Array<Scalars['String']>;
  latestMaterialization: Maybe<MaterializationEvent>;
  latestRun: Maybe<Run>;
  unstartedRunIds: Array<Scalars['String']>;
};

export type AssetLineageInfo = {
  __typename: 'AssetLineageInfo';
  assetKey: AssetKey;
  partitions: Array<Scalars['String']>;
};

export type AssetMaterializationPlannedEvent = MessageEvent &
  RunEvent & {
    __typename: 'AssetMaterializationPlannedEvent';
    assetKey: Maybe<AssetKey>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type AssetMetadataEntry = MetadataEntry & {
  __typename: 'AssetMetadataEntry';
  assetKey: AssetKey;
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
};

export type AssetNode = {
  __typename: 'AssetNode';
  assetKey: AssetKey;
  assetMaterializationUsedData: Array<MaterializationUpstreamDataVersion>;
  assetMaterializations: Array<MaterializationEvent>;
  assetObservations: Array<ObservationEvent>;
  assetPartitionStatuses: AssetPartitionStatuses;
  computeKind: Maybe<Scalars['String']>;
  configField: Maybe<ConfigTypeField>;
  currentDataVersion: Maybe<Scalars['String']>;
  dependedBy: Array<AssetDependency>;
  dependedByKeys: Array<AssetKey>;
  dependencies: Array<AssetDependency>;
  dependencyKeys: Array<AssetKey>;
  description: Maybe<Scalars['String']>;
  freshnessInfo: Maybe<AssetFreshnessInfo>;
  freshnessPolicy: Maybe<FreshnessPolicy>;
  graphName: Maybe<Scalars['String']>;
  groupName: Maybe<Scalars['String']>;
  hasMaterializePermission: Scalars['Boolean'];
  id: Scalars['ID'];
  isObservable: Scalars['Boolean'];
  isPartitioned: Scalars['Boolean'];
  isSource: Scalars['Boolean'];
  jobNames: Array<Scalars['String']>;
  jobs: Array<Pipeline>;
  latestMaterializationByPartition: Array<Maybe<MaterializationEvent>>;
  latestRunForPartition: Maybe<Run>;
  metadataEntries: Array<MetadataEntry>;
  op: Maybe<SolidDefinition>;
  opName: Maybe<Scalars['String']>;
  opNames: Array<Scalars['String']>;
  opVersion: Maybe<Scalars['String']>;
  partitionDefinition: Maybe<PartitionDefinition>;
  partitionKeys: Array<Scalars['String']>;
  partitionKeysByDimension: Array<DimensionPartitionKeys>;
  partitionStats: Maybe<PartitionStats>;
  repository: Repository;
  requiredResources: Array<ResourceRequirement>;
  staleCauses: Array<StaleCause>;
  staleStatus: Maybe<StaleStatus>;
  type: Maybe<DagsterType>;
};

export type AssetNodeAssetMaterializationUsedDataArgs = {
  timestampMillis: Scalars['String'];
};

export type AssetNodeAssetMaterializationsArgs = {
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
};

export type AssetNodeAssetObservationsArgs = {
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
};

export type AssetNodeLatestMaterializationByPartitionArgs = {
  partitions?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
};

export type AssetNodeLatestRunForPartitionArgs = {
  partition: Scalars['String'];
};

export type AssetNodePartitionKeysByDimensionArgs = {
  endIdx?: InputMaybe<Scalars['Int']>;
  startIdx?: InputMaybe<Scalars['Int']>;
};

export type AssetNodeDefinitionCollision = {
  __typename: 'AssetNodeDefinitionCollision';
  assetKey: AssetKey;
  repositories: Array<Repository>;
};

export type AssetNodeOrError = AssetNode | AssetNotFoundError;

export type AssetNotFoundError = Error & {
  __typename: 'AssetNotFoundError';
  message: Scalars['String'];
};

export type AssetOrError = Asset | AssetNotFoundError;

export type AssetPartitionStatuses = DefaultPartitions | MultiPartitions | TimePartitions;

export type AssetWipeMutationResult =
  | AssetNotFoundError
  | AssetWipeSuccess
  | PythonError
  | UnauthorizedError;

export type AssetWipeSuccess = {
  __typename: 'AssetWipeSuccess';
  assetKeys: Array<AssetKey>;
};

export type AssetsOrError = AssetConnection | PythonError;

export type BoolMetadataEntry = MetadataEntry & {
  __typename: 'BoolMetadataEntry';
  boolValue: Maybe<Scalars['Boolean']>;
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
};

export enum BulkActionStatus {
  CANCELED = 'CANCELED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  REQUESTED = 'REQUESTED',
}

export type CancelBackfillResult = CancelBackfillSuccess | PythonError | UnauthorizedError;

export type CancelBackfillSuccess = {
  __typename: 'CancelBackfillSuccess';
  backfillId: Scalars['String'];
};

export type CapturedLogs = {
  __typename: 'CapturedLogs';
  cursor: Maybe<Scalars['String']>;
  logKey: Array<Scalars['String']>;
  stderr: Maybe<Scalars['String']>;
  stdout: Maybe<Scalars['String']>;
};

export type CapturedLogsMetadata = {
  __typename: 'CapturedLogsMetadata';
  stderrDownloadUrl: Maybe<Scalars['String']>;
  stderrLocation: Maybe<Scalars['String']>;
  stdoutDownloadUrl: Maybe<Scalars['String']>;
  stdoutLocation: Maybe<Scalars['String']>;
};

export type CompositeConfigType = ConfigType & {
  __typename: 'CompositeConfigType';
  description: Maybe<Scalars['String']>;
  fields: Array<ConfigTypeField>;
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
};

export type CompositeSolidDefinition = ISolidDefinition &
  SolidContainer & {
    __typename: 'CompositeSolidDefinition';
    assetNodes: Array<AssetNode>;
    description: Maybe<Scalars['String']>;
    id: Scalars['ID'];
    inputDefinitions: Array<InputDefinition>;
    inputMappings: Array<InputMapping>;
    metadata: Array<MetadataItemDefinition>;
    modes: Array<Mode>;
    name: Scalars['String'];
    outputDefinitions: Array<OutputDefinition>;
    outputMappings: Array<OutputMapping>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
  };

export type CompositeSolidDefinitionSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type CompositeSolidDefinitionSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export enum ComputeIoType {
  STDERR = 'STDERR',
  STDOUT = 'STDOUT',
}

export type ComputeLogFile = {
  __typename: 'ComputeLogFile';
  cursor: Scalars['Int'];
  data: Maybe<Scalars['String']>;
  downloadUrl: Maybe<Scalars['String']>;
  path: Scalars['String'];
  size: Scalars['Int'];
};

export type ComputeLogs = {
  __typename: 'ComputeLogs';
  runId: Scalars['String'];
  stderr: Maybe<ComputeLogFile>;
  stdout: Maybe<ComputeLogFile>;
  stepKey: Scalars['String'];
};

export type ConfigType = {
  description: Maybe<Scalars['String']>;
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
};

export type ConfigTypeField = {
  __typename: 'ConfigTypeField';
  configType: ConfigType;
  configTypeKey: Scalars['String'];
  defaultValueAsJson: Maybe<Scalars['String']>;
  description: Maybe<Scalars['String']>;
  isRequired: Scalars['Boolean'];
  name: Scalars['String'];
};

export type ConfigTypeNotFoundError = Error & {
  __typename: 'ConfigTypeNotFoundError';
  configTypeName: Scalars['String'];
  message: Scalars['String'];
  pipeline: Pipeline;
};

export type ConfigTypeOrError =
  | CompositeConfigType
  | ConfigTypeNotFoundError
  | EnumConfigType
  | PipelineNotFoundError
  | PythonError
  | RegularConfigType;

export type ConfiguredValue = {
  __typename: 'ConfiguredValue';
  key: Scalars['String'];
  type: ConfiguredValueType;
  value: Scalars['String'];
};

export enum ConfiguredValueType {
  ENV_VAR = 'ENV_VAR',
  VALUE = 'VALUE',
}

export type ConflictingExecutionParamsError = Error & {
  __typename: 'ConflictingExecutionParamsError';
  message: Scalars['String'];
};

export type DaemonHealth = {
  __typename: 'DaemonHealth';
  allDaemonStatuses: Array<DaemonStatus>;
  daemonStatus: DaemonStatus;
  id: Scalars['String'];
};

export type DaemonHealthDaemonStatusArgs = {
  daemonType?: InputMaybe<Scalars['String']>;
};

export type DaemonStatus = {
  __typename: 'DaemonStatus';
  daemonType: Scalars['String'];
  healthy: Maybe<Scalars['Boolean']>;
  id: Scalars['ID'];
  lastHeartbeatErrors: Array<PythonError>;
  lastHeartbeatTime: Maybe<Scalars['Float']>;
  required: Scalars['Boolean'];
};

export type DagitMutation = {
  __typename: 'DagitMutation';
  addDynamicPartition: AddDynamicPartitionResult;
  cancelPartitionBackfill: CancelBackfillResult;
  deletePipelineRun: DeletePipelineRunResult;
  deleteRun: DeletePipelineRunResult;
  launchPartitionBackfill: LaunchBackfillResult;
  launchPipelineExecution: LaunchRunResult;
  launchPipelineReexecution: LaunchRunReexecutionResult;
  launchRun: LaunchRunResult;
  launchRunReexecution: LaunchRunReexecutionResult;
  logTelemetry: LogTelemetryMutationResult;
  reloadRepositoryLocation: ReloadRepositoryLocationMutationResult;
  reloadWorkspace: ReloadWorkspaceMutationResult;
  resumePartitionBackfill: ResumeBackfillResult;
  scheduleDryRun: ScheduleDryRunResult;
  sensorDryRun: SensorDryRunResult;
  setNuxSeen: Scalars['Boolean'];
  setSensorCursor: SensorOrError;
  shutdownRepositoryLocation: ShutdownRepositoryLocationMutationResult;
  startSchedule: ScheduleMutationResult;
  startSensor: SensorOrError;
  stopRunningSchedule: ScheduleMutationResult;
  stopSensor: StopSensorMutationResultOrError;
  terminatePipelineExecution: TerminateRunResult;
  terminateRun: TerminateRunResult;
  wipeAssets: AssetWipeMutationResult;
};

export type DagitMutationAddDynamicPartitionArgs = {
  partitionKey: Scalars['String'];
  partitionsDefName: Scalars['String'];
  repositorySelector: RepositorySelector;
};

export type DagitMutationCancelPartitionBackfillArgs = {
  backfillId: Scalars['String'];
};

export type DagitMutationDeletePipelineRunArgs = {
  runId: Scalars['String'];
};

export type DagitMutationDeleteRunArgs = {
  runId: Scalars['String'];
};

export type DagitMutationLaunchPartitionBackfillArgs = {
  backfillParams: LaunchBackfillParams;
};

export type DagitMutationLaunchPipelineExecutionArgs = {
  executionParams: ExecutionParams;
};

export type DagitMutationLaunchPipelineReexecutionArgs = {
  executionParams?: InputMaybe<ExecutionParams>;
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

export type DagitMutationLaunchRunArgs = {
  executionParams: ExecutionParams;
};

export type DagitMutationLaunchRunReexecutionArgs = {
  executionParams?: InputMaybe<ExecutionParams>;
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

export type DagitMutationLogTelemetryArgs = {
  action: Scalars['String'];
  clientId: Scalars['String'];
  clientTime: Scalars['String'];
  metadata: Scalars['String'];
};

export type DagitMutationReloadRepositoryLocationArgs = {
  repositoryLocationName: Scalars['String'];
};

export type DagitMutationResumePartitionBackfillArgs = {
  backfillId: Scalars['String'];
};

export type DagitMutationScheduleDryRunArgs = {
  selectorData: ScheduleSelector;
  timestamp?: InputMaybe<Scalars['Float']>;
};

export type DagitMutationSensorDryRunArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  selectorData: SensorSelector;
};

export type DagitMutationSetSensorCursorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  sensorSelector: SensorSelector;
};

export type DagitMutationShutdownRepositoryLocationArgs = {
  repositoryLocationName: Scalars['String'];
};

export type DagitMutationStartScheduleArgs = {
  scheduleSelector: ScheduleSelector;
};

export type DagitMutationStartSensorArgs = {
  sensorSelector: SensorSelector;
};

export type DagitMutationStopRunningScheduleArgs = {
  scheduleOriginId: Scalars['String'];
  scheduleSelectorId: Scalars['String'];
};

export type DagitMutationStopSensorArgs = {
  jobOriginId: Scalars['String'];
  jobSelectorId: Scalars['String'];
};

export type DagitMutationTerminatePipelineExecutionArgs = {
  runId: Scalars['String'];
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

export type DagitMutationTerminateRunArgs = {
  runId: Scalars['String'];
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

export type DagitMutationWipeAssetsArgs = {
  assetKeys: Array<AssetKeyInput>;
};

export type DagitQuery = {
  __typename: 'DagitQuery';
  allTopLevelResourceDetailsOrError: ResourcesOrError;
  assetNodeDefinitionCollisions: Array<AssetNodeDefinitionCollision>;
  assetNodeOrError: AssetNodeOrError;
  assetNodes: Array<AssetNode>;
  assetOrError: AssetOrError;
  assetsLatestInfo: Array<AssetLatestInfo>;
  assetsOrError: AssetsOrError;
  capturedLogs: CapturedLogs;
  capturedLogsMetadata: CapturedLogsMetadata;
  executionPlanOrError: ExecutionPlanOrError;
  graphOrError: GraphOrError;
  instance: Instance;
  instigationStateOrError: InstigationStateOrError;
  isPipelineConfigValid: PipelineConfigValidationResult;
  locationStatusesOrError: WorkspaceLocationStatusEntriesOrError;
  logsForRun: EventConnectionOrError;
  partitionBackfillOrError: PartitionBackfillOrError;
  partitionBackfillsOrError: PartitionBackfillsOrError;
  partitionSetOrError: PartitionSetOrError;
  partitionSetsOrError: PartitionSetsOrError;
  permissions: Array<Permission>;
  pipelineOrError: PipelineOrError;
  pipelineRunOrError: RunOrError;
  pipelineRunsOrError: RunsOrError;
  pipelineSnapshotOrError: PipelineSnapshotOrError;
  repositoriesOrError: RepositoriesOrError;
  repositoryOrError: RepositoryOrError;
  runConfigSchemaOrError: RunConfigSchemaOrError;
  runGroupOrError: RunGroupOrError;
  runGroupsOrError: RunGroupsOrError;
  runOrError: RunOrError;
  runTagKeysOrError: Maybe<RunTagKeysOrError>;
  runTagsOrError: Maybe<RunTagsOrError>;
  runsOrError: RunsOrError;
  scheduleOrError: ScheduleOrError;
  scheduler: SchedulerOrError;
  schedulesOrError: SchedulesOrError;
  sensorOrError: SensorOrError;
  sensorsOrError: SensorsOrError;
  shouldShowNux: Scalars['Boolean'];
  test: Maybe<TestFields>;
  topLevelResourceDetailsOrError: ResourceDetailsOrError;
  unloadableInstigationStatesOrError: InstigationStatesOrError;
  utilizedEnvVarsOrError: EnvVarWithConsumersOrError;
  version: Scalars['String'];
  workspaceOrError: WorkspaceOrError;
};

export type DagitQueryAllTopLevelResourceDetailsOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type DagitQueryAssetNodeDefinitionCollisionsArgs = {
  assetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type DagitQueryAssetNodeOrErrorArgs = {
  assetKey: AssetKeyInput;
};

export type DagitQueryAssetNodesArgs = {
  assetKeys?: InputMaybe<Array<AssetKeyInput>>;
  group?: InputMaybe<AssetGroupSelector>;
  loadMaterializations?: InputMaybe<Scalars['Boolean']>;
  pipeline?: InputMaybe<PipelineSelector>;
};

export type DagitQueryAssetOrErrorArgs = {
  assetKey: AssetKeyInput;
};

export type DagitQueryAssetsLatestInfoArgs = {
  assetKeys: Array<AssetKeyInput>;
};

export type DagitQueryAssetsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  prefix?: InputMaybe<Array<Scalars['String']>>;
};

export type DagitQueryCapturedLogsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  logKey: Array<Scalars['String']>;
};

export type DagitQueryCapturedLogsMetadataArgs = {
  logKey: Array<Scalars['String']>;
};

export type DagitQueryExecutionPlanOrErrorArgs = {
  mode: Scalars['String'];
  pipeline: PipelineSelector;
  runConfigData?: InputMaybe<Scalars['RunConfigData']>;
};

export type DagitQueryGraphOrErrorArgs = {
  selector?: InputMaybe<GraphSelector>;
};

export type DagitQueryInstigationStateOrErrorArgs = {
  instigationSelector: InstigationSelector;
};

export type DagitQueryIsPipelineConfigValidArgs = {
  mode: Scalars['String'];
  pipeline: PipelineSelector;
  runConfigData?: InputMaybe<Scalars['RunConfigData']>;
};

export type DagitQueryLogsForRunArgs = {
  afterCursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  runId: Scalars['ID'];
};

export type DagitQueryPartitionBackfillOrErrorArgs = {
  backfillId: Scalars['String'];
};

export type DagitQueryPartitionBackfillsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  status?: InputMaybe<BulkActionStatus>;
};

export type DagitQueryPartitionSetOrErrorArgs = {
  partitionSetName?: InputMaybe<Scalars['String']>;
  repositorySelector: RepositorySelector;
};

export type DagitQueryPartitionSetsOrErrorArgs = {
  pipelineName: Scalars['String'];
  repositorySelector: RepositorySelector;
};

export type DagitQueryPipelineOrErrorArgs = {
  params: PipelineSelector;
};

export type DagitQueryPipelineRunOrErrorArgs = {
  runId: Scalars['ID'];
};

export type DagitQueryPipelineRunsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type DagitQueryPipelineSnapshotOrErrorArgs = {
  activePipelineSelector?: InputMaybe<PipelineSelector>;
  snapshotId?: InputMaybe<Scalars['String']>;
};

export type DagitQueryRepositoriesOrErrorArgs = {
  repositorySelector?: InputMaybe<RepositorySelector>;
};

export type DagitQueryRepositoryOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type DagitQueryRunConfigSchemaOrErrorArgs = {
  mode?: InputMaybe<Scalars['String']>;
  selector: PipelineSelector;
};

export type DagitQueryRunGroupOrErrorArgs = {
  runId: Scalars['ID'];
};

export type DagitQueryRunGroupsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type DagitQueryRunOrErrorArgs = {
  runId: Scalars['ID'];
};

export type DagitQueryRunTagsOrErrorArgs = {
  limit?: InputMaybe<Scalars['Int']>;
  tagKeys?: InputMaybe<Array<Scalars['String']>>;
  valuePrefix?: InputMaybe<Scalars['String']>;
};

export type DagitQueryRunsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type DagitQueryScheduleOrErrorArgs = {
  scheduleSelector: ScheduleSelector;
};

export type DagitQuerySchedulesOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type DagitQuerySensorOrErrorArgs = {
  sensorSelector: SensorSelector;
};

export type DagitQuerySensorsOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type DagitQueryTopLevelResourceDetailsOrErrorArgs = {
  resourceSelector: ResourceSelector;
};

export type DagitQueryUnloadableInstigationStatesOrErrorArgs = {
  instigationType?: InputMaybe<InstigationType>;
};

export type DagitQueryUtilizedEnvVarsOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type DagitSubscription = {
  __typename: 'DagitSubscription';
  capturedLogs: CapturedLogs;
  computeLogs: ComputeLogFile;
  locationStateChangeEvents: LocationStateChangeSubscription;
  pipelineRunLogs: PipelineRunLogsSubscriptionPayload;
};

export type DagitSubscriptionCapturedLogsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  logKey: Array<Scalars['String']>;
};

export type DagitSubscriptionComputeLogsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  ioType: ComputeIoType;
  runId: Scalars['ID'];
  stepKey: Scalars['String'];
};

export type DagitSubscriptionPipelineRunLogsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  runId: Scalars['ID'];
};

export enum DagsterEventType {
  ALERT_FAILURE = 'ALERT_FAILURE',
  ALERT_START = 'ALERT_START',
  ALERT_SUCCESS = 'ALERT_SUCCESS',
  ASSET_MATERIALIZATION = 'ASSET_MATERIALIZATION',
  ASSET_MATERIALIZATION_PLANNED = 'ASSET_MATERIALIZATION_PLANNED',
  ASSET_OBSERVATION = 'ASSET_OBSERVATION',
  ASSET_STORE_OPERATION = 'ASSET_STORE_OPERATION',
  ENGINE_EVENT = 'ENGINE_EVENT',
  HANDLED_OUTPUT = 'HANDLED_OUTPUT',
  HOOK_COMPLETED = 'HOOK_COMPLETED',
  HOOK_ERRORED = 'HOOK_ERRORED',
  HOOK_SKIPPED = 'HOOK_SKIPPED',
  LOADED_INPUT = 'LOADED_INPUT',
  LOGS_CAPTURED = 'LOGS_CAPTURED',
  OBJECT_STORE_OPERATION = 'OBJECT_STORE_OPERATION',
  PIPELINE_CANCELED = 'PIPELINE_CANCELED',
  PIPELINE_CANCELING = 'PIPELINE_CANCELING',
  PIPELINE_DEQUEUED = 'PIPELINE_DEQUEUED',
  PIPELINE_ENQUEUED = 'PIPELINE_ENQUEUED',
  PIPELINE_FAILURE = 'PIPELINE_FAILURE',
  PIPELINE_START = 'PIPELINE_START',
  PIPELINE_STARTING = 'PIPELINE_STARTING',
  PIPELINE_SUCCESS = 'PIPELINE_SUCCESS',
  RESOURCE_INIT_FAILURE = 'RESOURCE_INIT_FAILURE',
  RESOURCE_INIT_STARTED = 'RESOURCE_INIT_STARTED',
  RESOURCE_INIT_SUCCESS = 'RESOURCE_INIT_SUCCESS',
  RUN_CANCELED = 'RUN_CANCELED',
  RUN_CANCELING = 'RUN_CANCELING',
  RUN_DEQUEUED = 'RUN_DEQUEUED',
  RUN_ENQUEUED = 'RUN_ENQUEUED',
  RUN_FAILURE = 'RUN_FAILURE',
  RUN_START = 'RUN_START',
  RUN_STARTING = 'RUN_STARTING',
  RUN_SUCCESS = 'RUN_SUCCESS',
  STEP_EXPECTATION_RESULT = 'STEP_EXPECTATION_RESULT',
  STEP_FAILURE = 'STEP_FAILURE',
  STEP_INPUT = 'STEP_INPUT',
  STEP_OUTPUT = 'STEP_OUTPUT',
  STEP_RESTARTED = 'STEP_RESTARTED',
  STEP_SKIPPED = 'STEP_SKIPPED',
  STEP_START = 'STEP_START',
  STEP_SUCCESS = 'STEP_SUCCESS',
  STEP_UP_FOR_RETRY = 'STEP_UP_FOR_RETRY',
  STEP_WORKER_STARTED = 'STEP_WORKER_STARTED',
  STEP_WORKER_STARTING = 'STEP_WORKER_STARTING',
}

export type DagsterLibraryVersion = {
  __typename: 'DagsterLibraryVersion';
  name: Scalars['String'];
  version: Scalars['String'];
};

export type DagsterRunEvent =
  | AlertFailureEvent
  | AlertStartEvent
  | AlertSuccessEvent
  | AssetMaterializationPlannedEvent
  | EngineEvent
  | ExecutionStepFailureEvent
  | ExecutionStepInputEvent
  | ExecutionStepOutputEvent
  | ExecutionStepRestartEvent
  | ExecutionStepSkippedEvent
  | ExecutionStepStartEvent
  | ExecutionStepSuccessEvent
  | ExecutionStepUpForRetryEvent
  | HandledOutputEvent
  | HookCompletedEvent
  | HookErroredEvent
  | HookSkippedEvent
  | LoadedInputEvent
  | LogMessageEvent
  | LogsCapturedEvent
  | MaterializationEvent
  | ObjectStoreOperationEvent
  | ObservationEvent
  | ResourceInitFailureEvent
  | ResourceInitStartedEvent
  | ResourceInitSuccessEvent
  | RunCanceledEvent
  | RunCancelingEvent
  | RunDequeuedEvent
  | RunEnqueuedEvent
  | RunFailureEvent
  | RunStartEvent
  | RunStartingEvent
  | RunSuccessEvent
  | StepExpectationResultEvent
  | StepWorkerStartedEvent
  | StepWorkerStartingEvent;

export type DagsterType = {
  description: Maybe<Scalars['String']>;
  displayName: Scalars['String'];
  innerTypes: Array<DagsterType>;
  inputSchemaType: Maybe<ConfigType>;
  isBuiltin: Scalars['Boolean'];
  isList: Scalars['Boolean'];
  isNothing: Scalars['Boolean'];
  isNullable: Scalars['Boolean'];
  key: Scalars['String'];
  metadataEntries: Array<MetadataEntry>;
  name: Maybe<Scalars['String']>;
  outputSchemaType: Maybe<ConfigType>;
};

export type DagsterTypeNotFoundError = Error & {
  __typename: 'DagsterTypeNotFoundError';
  dagsterTypeName: Scalars['String'];
  message: Scalars['String'];
};

export type DagsterTypeOrError =
  | DagsterTypeNotFoundError
  | PipelineNotFoundError
  | PythonError
  | RegularDagsterType;

export type DefaultPartitions = {
  __typename: 'DefaultPartitions';
  failedPartitions: Array<Scalars['String']>;
  materializedPartitions: Array<Scalars['String']>;
  unmaterializedPartitions: Array<Scalars['String']>;
};

export type DeletePipelineRunResult =
  | DeletePipelineRunSuccess
  | PythonError
  | RunNotFoundError
  | UnauthorizedError;

export type DeletePipelineRunSuccess = {
  __typename: 'DeletePipelineRunSuccess';
  runId: Scalars['String'];
};

export type DeleteRunMutation = {
  __typename: 'DeleteRunMutation';
  Output: DeletePipelineRunResult;
};

export type DimensionDefinitionType = {
  __typename: 'DimensionDefinitionType';
  description: Scalars['String'];
  isPrimaryDimension: Scalars['Boolean'];
  name: Scalars['String'];
  type: PartitionDefinitionType;
};

export type DimensionPartitionKeys = {
  __typename: 'DimensionPartitionKeys';
  name: Scalars['String'];
  partitionKeys: Array<Scalars['String']>;
  type: PartitionDefinitionType;
};

export type DisplayableEvent = {
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
};

export type DryRunInstigationTick = {
  __typename: 'DryRunInstigationTick';
  evaluationResult: Maybe<TickEvaluation>;
  timestamp: Maybe<Scalars['Float']>;
};

export type DryRunInstigationTicks = {
  __typename: 'DryRunInstigationTicks';
  cursor: Scalars['Float'];
  results: Array<DryRunInstigationTick>;
};

export type DuplicateDynamicPartitionError = Error & {
  __typename: 'DuplicateDynamicPartitionError';
  message: Scalars['String'];
  partitionName: Scalars['String'];
  partitionsDefName: Scalars['String'];
};

export type EngineEvent = DisplayableEvent &
  ErrorEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'EngineEvent';
    description: Maybe<Scalars['String']>;
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type EnumConfigType = ConfigType & {
  __typename: 'EnumConfigType';
  description: Maybe<Scalars['String']>;
  givenName: Scalars['String'];
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
  values: Array<EnumConfigValue>;
};

export type EnumConfigValue = {
  __typename: 'EnumConfigValue';
  description: Maybe<Scalars['String']>;
  value: Scalars['String'];
};

export type EnvVarConsumer = {
  __typename: 'EnvVarConsumer';
  name: Scalars['String'];
  type: EnvVarConsumerType;
};

export enum EnvVarConsumerType {
  RESOURCE = 'RESOURCE',
}

export type EnvVarWithConsumers = {
  __typename: 'EnvVarWithConsumers';
  envVarConsumers: Array<EnvVarConsumer>;
  envVarName: Scalars['String'];
};

export type EnvVarWithConsumersList = {
  __typename: 'EnvVarWithConsumersList';
  results: Array<EnvVarWithConsumers>;
};

export type EnvVarWithConsumersOrError = EnvVarWithConsumersList | PythonError;

export type Error = {
  message: Scalars['String'];
};

export type ErrorChainLink = Error & {
  __typename: 'ErrorChainLink';
  error: PythonError;
  isExplicitLink: Scalars['Boolean'];
  message: Scalars['String'];
};

export type ErrorEvent = {
  error: Maybe<PythonError>;
};

export enum ErrorSource {
  FRAMEWORK_ERROR = 'FRAMEWORK_ERROR',
  INTERRUPT = 'INTERRUPT',
  UNEXPECTED_ERROR = 'UNEXPECTED_ERROR',
  USER_CODE_ERROR = 'USER_CODE_ERROR',
}

export enum EvaluationErrorReason {
  FIELDS_NOT_DEFINED = 'FIELDS_NOT_DEFINED',
  FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED',
  MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD',
  MISSING_REQUIRED_FIELDS = 'MISSING_REQUIRED_FIELDS',
  RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH',
  SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR',
}

export type EvaluationStack = {
  __typename: 'EvaluationStack';
  entries: Array<EvaluationStackEntry>;
};

export type EvaluationStackEntry =
  | EvaluationStackListItemEntry
  | EvaluationStackMapKeyEntry
  | EvaluationStackMapValueEntry
  | EvaluationStackPathEntry;

export type EvaluationStackListItemEntry = {
  __typename: 'EvaluationStackListItemEntry';
  listIndex: Scalars['Int'];
};

export type EvaluationStackMapKeyEntry = {
  __typename: 'EvaluationStackMapKeyEntry';
  mapKey: Scalars['GenericScalar'];
};

export type EvaluationStackMapValueEntry = {
  __typename: 'EvaluationStackMapValueEntry';
  mapKey: Scalars['GenericScalar'];
};

export type EvaluationStackPathEntry = {
  __typename: 'EvaluationStackPathEntry';
  fieldName: Scalars['String'];
};

export type EventConnection = {
  __typename: 'EventConnection';
  cursor: Scalars['String'];
  events: Array<DagsterRunEvent>;
  hasMore: Scalars['Boolean'];
};

export type EventConnectionOrError = EventConnection | PythonError | RunNotFoundError;

export type EventTag = {
  __typename: 'EventTag';
  key: Scalars['String'];
  value: Scalars['String'];
};

export type ExecutionMetadata = {
  parentRunId?: InputMaybe<Scalars['String']>;
  rootRunId?: InputMaybe<Scalars['String']>;
  runId?: InputMaybe<Scalars['String']>;
  tags?: InputMaybe<Array<ExecutionTag>>;
};

export type ExecutionParams = {
  executionMetadata?: InputMaybe<ExecutionMetadata>;
  mode?: InputMaybe<Scalars['String']>;
  preset?: InputMaybe<Scalars['String']>;
  runConfigData?: InputMaybe<Scalars['RunConfigData']>;
  selector: JobOrPipelineSelector;
  stepKeys?: InputMaybe<Array<Scalars['String']>>;
};

export type ExecutionPlan = {
  __typename: 'ExecutionPlan';
  artifactsPersisted: Scalars['Boolean'];
  steps: Array<ExecutionStep>;
};

export type ExecutionPlanOrError =
  | ExecutionPlan
  | InvalidSubsetError
  | PipelineNotFoundError
  | PythonError
  | RunConfigValidationInvalid;

export type ExecutionStep = {
  __typename: 'ExecutionStep';
  inputs: Array<ExecutionStepInput>;
  key: Scalars['String'];
  kind: StepKind;
  metadata: Array<MetadataItemDefinition>;
  outputs: Array<ExecutionStepOutput>;
  solidHandleID: Scalars['String'];
};

export type ExecutionStepFailureEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepFailureEvent';
    error: Maybe<PythonError>;
    errorSource: Maybe<ErrorSource>;
    eventType: Maybe<DagsterEventType>;
    failureMetadata: Maybe<FailureMetadata>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepInput = {
  __typename: 'ExecutionStepInput';
  dependsOn: Array<ExecutionStep>;
  name: Scalars['String'];
};

export type ExecutionStepInputEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepInputEvent';
    eventType: Maybe<DagsterEventType>;
    inputName: Scalars['String'];
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
    typeCheck: TypeCheck;
  };

export type ExecutionStepOutput = {
  __typename: 'ExecutionStepOutput';
  name: Scalars['String'];
};

export type ExecutionStepOutputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepOutputEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    outputName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
    typeCheck: TypeCheck;
  };

export type ExecutionStepRestartEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepRestartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepSkippedEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepSkippedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepStartEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepStartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepSuccessEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepSuccessEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionStepUpForRetryEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepUpForRetryEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    secondsToWait: Maybe<Scalars['Int']>;
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ExecutionTag = {
  key: Scalars['String'];
  value: Scalars['String'];
};

export type ExpectationResult = DisplayableEvent & {
  __typename: 'ExpectationResult';
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
  success: Scalars['Boolean'];
};

export type FailureMetadata = DisplayableEvent & {
  __typename: 'FailureMetadata';
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
};

export type FieldNotDefinedConfigError = PipelineConfigValidationError & {
  __typename: 'FieldNotDefinedConfigError';
  fieldName: Scalars['String'];
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type FieldsNotDefinedConfigError = PipelineConfigValidationError & {
  __typename: 'FieldsNotDefinedConfigError';
  fieldNames: Array<Scalars['String']>;
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type FloatMetadataEntry = MetadataEntry & {
  __typename: 'FloatMetadataEntry';
  description: Maybe<Scalars['String']>;
  floatValue: Maybe<Scalars['Float']>;
  label: Scalars['String'];
};

export type FreshnessPolicy = {
  __typename: 'FreshnessPolicy';
  cronSchedule: Maybe<Scalars['String']>;
  cronScheduleTimezone: Maybe<Scalars['String']>;
  maximumLagMinutes: Scalars['Float'];
};

export type Graph = SolidContainer & {
  __typename: 'Graph';
  description: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  modes: Array<Mode>;
  name: Scalars['String'];
  solidHandle: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
};

export type GraphSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type GraphSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type GraphNotFoundError = Error & {
  __typename: 'GraphNotFoundError';
  graphName: Scalars['String'];
  message: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type GraphOrError = Graph | GraphNotFoundError | PythonError;

export type GraphSelector = {
  graphName: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type HandledOutputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'HandledOutputEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    managerKey: Scalars['String'];
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    outputName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type HookCompletedEvent = MessageEvent &
  StepEvent & {
    __typename: 'HookCompletedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type HookErroredEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'HookErroredEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type HookSkippedEvent = MessageEvent &
  StepEvent & {
    __typename: 'HookSkippedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type IPipelineSnapshot = {
  dagsterTypeOrError: DagsterTypeOrError;
  dagsterTypes: Array<DagsterType>;
  description: Maybe<Scalars['String']>;
  graphName: Scalars['String'];
  metadataEntries: Array<MetadataEntry>;
  modes: Array<Mode>;
  name: Scalars['String'];
  parentSnapshotId: Maybe<Scalars['String']>;
  pipelineSnapshotId: Scalars['String'];
  runs: Array<Run>;
  schedules: Array<Schedule>;
  sensors: Array<Sensor>;
  solidHandle: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
  tags: Array<PipelineTag>;
};

export type IPipelineSnapshotDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String'];
};

export type IPipelineSnapshotRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type IPipelineSnapshotSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type IPipelineSnapshotSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type ISolidDefinition = {
  assetNodes: Array<AssetNode>;
  description: Maybe<Scalars['String']>;
  inputDefinitions: Array<InputDefinition>;
  metadata: Array<MetadataItemDefinition>;
  name: Scalars['String'];
  outputDefinitions: Array<OutputDefinition>;
};

export type Input = {
  __typename: 'Input';
  definition: InputDefinition;
  dependsOn: Array<Output>;
  isDynamicCollect: Scalars['Boolean'];
  solid: Solid;
};

export type InputDefinition = {
  __typename: 'InputDefinition';
  description: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
  name: Scalars['String'];
  solidDefinition: SolidDefinition;
  type: DagsterType;
};

export type InputMapping = {
  __typename: 'InputMapping';
  definition: InputDefinition;
  mappedInput: Input;
};

export type InputTag = {
  name: Scalars['String'];
  value: Scalars['String'];
};

export type Instance = {
  __typename: 'Instance';
  daemonHealth: DaemonHealth;
  executablePath: Scalars['String'];
  hasCapturedLogManager: Scalars['Boolean'];
  hasInfo: Scalars['Boolean'];
  info: Maybe<Scalars['String']>;
  runLauncher: Maybe<RunLauncher>;
  runQueuingSupported: Scalars['Boolean'];
};

export type InstigationEvent = {
  __typename: 'InstigationEvent';
  level: LogLevel;
  message: Scalars['String'];
  timestamp: Scalars['String'];
};

export type InstigationEventConnection = {
  __typename: 'InstigationEventConnection';
  cursor: Scalars['String'];
  events: Array<InstigationEvent>;
  hasMore: Scalars['Boolean'];
};

export type InstigationSelector = {
  name: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type InstigationState = {
  __typename: 'InstigationState';
  hasStartPermission: Scalars['Boolean'];
  hasStopPermission: Scalars['Boolean'];
  id: Scalars['ID'];
  instigationType: InstigationType;
  name: Scalars['String'];
  nextTick: Maybe<DryRunInstigationTick>;
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  repositoryOrigin: RepositoryOrigin;
  runningCount: Scalars['Int'];
  runs: Array<Run>;
  runsCount: Scalars['Int'];
  selectorId: Scalars['String'];
  status: InstigationStatus;
  tick: Maybe<InstigationTick>;
  ticks: Array<InstigationTick>;
  typeSpecificData: Maybe<InstigationTypeSpecificData>;
};

export type InstigationStateRunsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type InstigationStateTickArgs = {
  timestamp?: InputMaybe<Scalars['Float']>;
};

export type InstigationStateTicksArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  dayOffset?: InputMaybe<Scalars['Int']>;
  dayRange?: InputMaybe<Scalars['Int']>;
  limit?: InputMaybe<Scalars['Int']>;
  statuses?: InputMaybe<Array<InstigationTickStatus>>;
};

export type InstigationStateNotFoundError = Error & {
  __typename: 'InstigationStateNotFoundError';
  message: Scalars['String'];
  name: Scalars['String'];
};

export type InstigationStateOrError =
  | InstigationState
  | InstigationStateNotFoundError
  | PythonError;

export type InstigationStates = {
  __typename: 'InstigationStates';
  results: Array<InstigationState>;
};

export type InstigationStatesOrError = InstigationStates | PythonError;

export enum InstigationStatus {
  RUNNING = 'RUNNING',
  STOPPED = 'STOPPED',
}

export type InstigationTick = {
  __typename: 'InstigationTick';
  cursor: Maybe<Scalars['String']>;
  error: Maybe<PythonError>;
  id: Scalars['ID'];
  logEvents: InstigationEventConnection;
  logKey: Maybe<Array<Scalars['String']>>;
  originRunIds: Array<Scalars['String']>;
  runIds: Array<Scalars['String']>;
  runKeys: Array<Scalars['String']>;
  runs: Array<Run>;
  skipReason: Maybe<Scalars['String']>;
  status: InstigationTickStatus;
  timestamp: Scalars['Float'];
};

export enum InstigationTickStatus {
  FAILURE = 'FAILURE',
  SKIPPED = 'SKIPPED',
  STARTED = 'STARTED',
  SUCCESS = 'SUCCESS',
}

export enum InstigationType {
  SCHEDULE = 'SCHEDULE',
  SENSOR = 'SENSOR',
}

export type InstigationTypeSpecificData = ScheduleData | SensorData;

export type IntMetadataEntry = MetadataEntry & {
  __typename: 'IntMetadataEntry';
  description: Maybe<Scalars['String']>;
  intRepr: Scalars['String'];
  intValue: Maybe<Scalars['Int']>;
  label: Scalars['String'];
};

export type InvalidOutputError = {
  __typename: 'InvalidOutputError';
  invalidOutputName: Scalars['String'];
  stepKey: Scalars['String'];
};

export type InvalidPipelineRunsFilterError = Error & {
  __typename: 'InvalidPipelineRunsFilterError';
  message: Scalars['String'];
};

export type InvalidStepError = {
  __typename: 'InvalidStepError';
  invalidStepKey: Scalars['String'];
};

export type InvalidSubsetError = Error & {
  __typename: 'InvalidSubsetError';
  message: Scalars['String'];
  pipeline: Pipeline;
};

export type Job = IPipelineSnapshot &
  SolidContainer & {
    __typename: 'Job';
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<DagsterType>;
    description: Maybe<Scalars['String']>;
    graphName: Scalars['String'];
    id: Scalars['ID'];
    isAssetJob: Scalars['Boolean'];
    isJob: Scalars['Boolean'];
    metadataEntries: Array<MetadataEntry>;
    modes: Array<Mode>;
    name: Scalars['String'];
    parentSnapshotId: Maybe<Scalars['String']>;
    pipelineSnapshotId: Scalars['String'];
    presets: Array<PipelinePreset>;
    repository: Repository;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type JobDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String'];
};

export type JobRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type JobSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type JobSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type JobOrPipelineSelector = {
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  jobName?: InputMaybe<Scalars['String']>;
  pipelineName?: InputMaybe<Scalars['String']>;
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  solidSelection?: InputMaybe<Array<Scalars['String']>>;
};

export type JsonMetadataEntry = MetadataEntry & {
  __typename: 'JsonMetadataEntry';
  description: Maybe<Scalars['String']>;
  jsonString: Scalars['String'];
  label: Scalars['String'];
};

export type LaunchBackfillMutation = {
  __typename: 'LaunchBackfillMutation';
  Output: LaunchBackfillResult;
};

export type LaunchBackfillParams = {
  allPartitions?: InputMaybe<Scalars['Boolean']>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  forceSynchronousSubmission?: InputMaybe<Scalars['Boolean']>;
  fromFailure?: InputMaybe<Scalars['Boolean']>;
  partitionNames?: InputMaybe<Array<Scalars['String']>>;
  reexecutionSteps?: InputMaybe<Array<Scalars['String']>>;
  selector?: InputMaybe<PartitionSetSelector>;
  tags?: InputMaybe<Array<ExecutionTag>>;
};

export type LaunchBackfillResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchBackfillSuccess
  | NoModeProvidedError
  | PartitionSetNotFoundError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchBackfillSuccess = {
  __typename: 'LaunchBackfillSuccess';
  backfillId: Scalars['String'];
  launchedRunIds: Maybe<Array<Maybe<Scalars['String']>>>;
};

export type LaunchPipelineRunSuccess = {
  run: Run;
};

export type LaunchRunMutation = {
  __typename: 'LaunchRunMutation';
  Output: LaunchRunResult;
};

export type LaunchRunReexecutionMutation = {
  __typename: 'LaunchRunReexecutionMutation';
  Output: LaunchRunReexecutionResult;
};

export type LaunchRunReexecutionResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchRunSuccess
  | NoModeProvidedError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchRunResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchRunSuccess
  | NoModeProvidedError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchRunSuccess = LaunchPipelineRunSuccess & {
  __typename: 'LaunchRunSuccess';
  run: Run;
};

export type ListDagsterType = DagsterType &
  WrappingDagsterType & {
    __typename: 'ListDagsterType';
    description: Maybe<Scalars['String']>;
    displayName: Scalars['String'];
    innerTypes: Array<DagsterType>;
    inputSchemaType: Maybe<ConfigType>;
    isBuiltin: Scalars['Boolean'];
    isList: Scalars['Boolean'];
    isNothing: Scalars['Boolean'];
    isNullable: Scalars['Boolean'];
    key: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    name: Maybe<Scalars['String']>;
    ofType: DagsterType;
    outputSchemaType: Maybe<ConfigType>;
  };

export type LoadedInputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'LoadedInputEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    inputName: Scalars['String'];
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    managerKey: Scalars['String'];
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
    upstreamOutputName: Maybe<Scalars['String']>;
    upstreamStepKey: Maybe<Scalars['String']>;
  };

export type LocationStateChangeEvent = {
  __typename: 'LocationStateChangeEvent';
  eventType: LocationStateChangeEventType;
  locationName: Scalars['String'];
  message: Scalars['String'];
  serverId: Maybe<Scalars['String']>;
};

export enum LocationStateChangeEventType {
  LOCATION_DISCONNECTED = 'LOCATION_DISCONNECTED',
  LOCATION_ERROR = 'LOCATION_ERROR',
  LOCATION_RECONNECTED = 'LOCATION_RECONNECTED',
  LOCATION_UPDATED = 'LOCATION_UPDATED',
}

export type LocationStateChangeSubscription = {
  __typename: 'LocationStateChangeSubscription';
  event: LocationStateChangeEvent;
};

export enum LogLevel {
  CRITICAL = 'CRITICAL',
  DEBUG = 'DEBUG',
  ERROR = 'ERROR',
  INFO = 'INFO',
  WARNING = 'WARNING',
}

export type LogMessageEvent = MessageEvent & {
  __typename: 'LogMessageEvent';
  eventType: Maybe<DagsterEventType>;
  level: LogLevel;
  message: Scalars['String'];
  runId: Scalars['String'];
  solidHandleID: Maybe<Scalars['String']>;
  stepKey: Maybe<Scalars['String']>;
  timestamp: Scalars['String'];
};

export type LogTelemetryMutationResult = LogTelemetrySuccess | PythonError;

export type LogTelemetrySuccess = {
  __typename: 'LogTelemetrySuccess';
  action: Scalars['String'];
};

export type Logger = {
  __typename: 'Logger';
  configField: Maybe<ConfigTypeField>;
  description: Maybe<Scalars['String']>;
  name: Scalars['String'];
};

export type LogsCapturedEvent = MessageEvent & {
  __typename: 'LogsCapturedEvent';
  eventType: Maybe<DagsterEventType>;
  externalUrl: Maybe<Scalars['String']>;
  fileKey: Scalars['String'];
  level: LogLevel;
  logKey: Scalars['String'];
  message: Scalars['String'];
  pid: Maybe<Scalars['Int']>;
  runId: Scalars['String'];
  solidHandleID: Maybe<Scalars['String']>;
  stepKey: Maybe<Scalars['String']>;
  stepKeys: Maybe<Array<Scalars['String']>>;
  timestamp: Scalars['String'];
};

export type MapConfigType = ConfigType & {
  __typename: 'MapConfigType';
  description: Maybe<Scalars['String']>;
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  keyLabelName: Maybe<Scalars['String']>;
  keyType: ConfigType;
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
  valueType: ConfigType;
};

export type MarkdownMetadataEntry = MetadataEntry & {
  __typename: 'MarkdownMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  mdStr: Scalars['String'];
};

export type MarkerEvent = {
  markerEnd: Maybe<Scalars['String']>;
  markerStart: Maybe<Scalars['String']>;
};

export type MarshalledInput = {
  inputName: Scalars['String'];
  key: Scalars['String'];
};

export type MarshalledOutput = {
  key: Scalars['String'];
  outputName: Scalars['String'];
};

export type MaterializationEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'MaterializationEvent';
    assetKey: Maybe<AssetKey>;
    assetLineage: Array<AssetLineageInfo>;
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    partition: Maybe<Scalars['String']>;
    runId: Scalars['String'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    stepStats: RunStepStats;
    tags: Array<EventTag>;
    timestamp: Scalars['String'];
  };

export type MaterializationUpstreamDataVersion = {
  __typename: 'MaterializationUpstreamDataVersion';
  assetKey: AssetKey;
  downstreamAssetKey: AssetKey;
  timestamp: Scalars['String'];
};

export type MaterializedPartitionRange2D = {
  __typename: 'MaterializedPartitionRange2D';
  primaryDimEndKey: Scalars['String'];
  primaryDimEndTime: Maybe<Scalars['Float']>;
  primaryDimStartKey: Scalars['String'];
  primaryDimStartTime: Maybe<Scalars['Float']>;
  secondaryDim: PartitionStatus1D;
};

export type MessageEvent = {
  eventType: Maybe<DagsterEventType>;
  level: LogLevel;
  message: Scalars['String'];
  runId: Scalars['String'];
  solidHandleID: Maybe<Scalars['String']>;
  stepKey: Maybe<Scalars['String']>;
  timestamp: Scalars['String'];
};

export type MetadataEntry = {
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
};

export type MetadataItemDefinition = {
  __typename: 'MetadataItemDefinition';
  key: Scalars['String'];
  value: Scalars['String'];
};

export type MissingFieldConfigError = PipelineConfigValidationError & {
  __typename: 'MissingFieldConfigError';
  field: ConfigTypeField;
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type MissingFieldsConfigError = PipelineConfigValidationError & {
  __typename: 'MissingFieldsConfigError';
  fields: Array<ConfigTypeField>;
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type MissingRunIdErrorEvent = {
  __typename: 'MissingRunIdErrorEvent';
  invalidRunId: Scalars['String'];
};

export type Mode = {
  __typename: 'Mode';
  description: Maybe<Scalars['String']>;
  id: Scalars['String'];
  loggers: Array<Logger>;
  name: Scalars['String'];
  resources: Array<Resource>;
};

export type ModeNotFoundError = Error & {
  __typename: 'ModeNotFoundError';
  message: Scalars['String'];
  mode: Scalars['String'];
};

export type MultiPartitions = {
  __typename: 'MultiPartitions';
  primaryDimensionName: Scalars['String'];
  ranges: Array<MaterializedPartitionRange2D>;
};

export type NoModeProvidedError = Error & {
  __typename: 'NoModeProvidedError';
  message: Scalars['String'];
  pipelineName: Scalars['String'];
};

export type NodeInvocationSite = {
  __typename: 'NodeInvocationSite';
  pipeline: Pipeline;
  solidHandle: SolidHandle;
};

export type NotebookMetadataEntry = MetadataEntry & {
  __typename: 'NotebookMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  path: Scalars['String'];
};

export type NullMetadataEntry = MetadataEntry & {
  __typename: 'NullMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
};

export type NullableConfigType = ConfigType &
  WrappingConfigType & {
    __typename: 'NullableConfigType';
    description: Maybe<Scalars['String']>;
    isSelector: Scalars['Boolean'];
    key: Scalars['String'];
    ofType: ConfigType;
    recursiveConfigTypes: Array<ConfigType>;
    typeParamKeys: Array<Scalars['String']>;
  };

export type NullableDagsterType = DagsterType &
  WrappingDagsterType & {
    __typename: 'NullableDagsterType';
    description: Maybe<Scalars['String']>;
    displayName: Scalars['String'];
    innerTypes: Array<DagsterType>;
    inputSchemaType: Maybe<ConfigType>;
    isBuiltin: Scalars['Boolean'];
    isList: Scalars['Boolean'];
    isNothing: Scalars['Boolean'];
    isNullable: Scalars['Boolean'];
    key: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    name: Maybe<Scalars['String']>;
    ofType: DagsterType;
    outputSchemaType: Maybe<ConfigType>;
  };

export type ObjectStoreOperationEvent = MessageEvent &
  StepEvent & {
    __typename: 'ObjectStoreOperationEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    operationResult: ObjectStoreOperationResult;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ObjectStoreOperationResult = DisplayableEvent & {
  __typename: 'ObjectStoreOperationResult';
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
  op: ObjectStoreOperationType;
};

export enum ObjectStoreOperationType {
  CP_OBJECT = 'CP_OBJECT',
  GET_OBJECT = 'GET_OBJECT',
  RM_OBJECT = 'RM_OBJECT',
  SET_OBJECT = 'SET_OBJECT',
}

export type ObservationEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ObservationEvent';
    assetKey: Maybe<AssetKey>;
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    partition: Maybe<Scalars['String']>;
    runId: Scalars['String'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    stepStats: RunStepStats;
    tags: Array<EventTag>;
    timestamp: Scalars['String'];
  };

export type Output = {
  __typename: 'Output';
  definition: OutputDefinition;
  dependedBy: Array<Input>;
  solid: Solid;
};

export type OutputDefinition = {
  __typename: 'OutputDefinition';
  description: Maybe<Scalars['String']>;
  isDynamic: Maybe<Scalars['Boolean']>;
  metadataEntries: Array<MetadataEntry>;
  name: Scalars['String'];
  solidDefinition: SolidDefinition;
  type: DagsterType;
};

export type OutputMapping = {
  __typename: 'OutputMapping';
  definition: OutputDefinition;
  mappedOutput: Output;
};

export type Partition = {
  __typename: 'Partition';
  mode: Scalars['String'];
  name: Scalars['String'];
  partitionSetName: Scalars['String'];
  runConfigOrError: PartitionRunConfigOrError;
  runs: Array<Run>;
  solidSelection: Maybe<Array<Scalars['String']>>;
  status: Maybe<RunStatus>;
  tagsOrError: PartitionTagsOrError;
};

export type PartitionRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionBackfill = {
  __typename: 'PartitionBackfill';
  assetSelection: Maybe<Array<AssetKey>>;
  backfillId: Scalars['String'];
  error: Maybe<PythonError>;
  fromFailure: Scalars['Boolean'];
  hasCancelPermission: Scalars['Boolean'];
  hasResumePermission: Scalars['Boolean'];
  isValidSerialization: Scalars['Boolean'];
  numCancelable: Scalars['Int'];
  numPartitions: Maybe<Scalars['Int']>;
  partitionNames: Maybe<Array<Scalars['String']>>;
  partitionSet: Maybe<PartitionSet>;
  partitionSetName: Maybe<Scalars['String']>;
  partitionStatusCounts: Array<PartitionStatusCounts>;
  partitionStatuses: PartitionStatuses;
  reexecutionSteps: Maybe<Array<Scalars['String']>>;
  runs: Array<Run>;
  status: BulkActionStatus;
  timestamp: Scalars['Float'];
  unfinishedRuns: Array<Run>;
};

export type PartitionBackfillRunsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionBackfillUnfinishedRunsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionBackfillOrError = PartitionBackfill | PythonError;

export type PartitionBackfills = {
  __typename: 'PartitionBackfills';
  results: Array<PartitionBackfill>;
};

export type PartitionBackfillsOrError = PartitionBackfills | PythonError;

export type PartitionDefinition = {
  __typename: 'PartitionDefinition';
  description: Scalars['String'];
  dimensionTypes: Array<DimensionDefinitionType>;
  name: Maybe<Scalars['String']>;
  timeWindowMetadata: Maybe<TimePartitionsDefinitionMetadata>;
  type: PartitionDefinitionType;
};

export enum PartitionDefinitionType {
  DYNAMIC = 'DYNAMIC',
  MULTIPARTITIONED = 'MULTIPARTITIONED',
  STATIC = 'STATIC',
  TIME_WINDOW = 'TIME_WINDOW',
}

export enum PartitionRangeStatus {
  FAILED = 'FAILED',
  MATERIALIZED = 'MATERIALIZED',
  MATERIALIZING = 'MATERIALIZING',
}

export type PartitionRun = {
  __typename: 'PartitionRun';
  id: Scalars['String'];
  partitionName: Scalars['String'];
  run: Maybe<Run>;
};

export type PartitionRunConfig = {
  __typename: 'PartitionRunConfig';
  yaml: Scalars['String'];
};

export type PartitionRunConfigOrError = PartitionRunConfig | PythonError;

export type PartitionSet = {
  __typename: 'PartitionSet';
  backfills: Array<PartitionBackfill>;
  id: Scalars['ID'];
  mode: Scalars['String'];
  name: Scalars['String'];
  partition: Maybe<Partition>;
  partitionRuns: Array<PartitionRun>;
  partitionStatusesOrError: PartitionStatusesOrError;
  partitionsOrError: PartitionsOrError;
  pipelineName: Scalars['String'];
  repositoryOrigin: RepositoryOrigin;
  solidSelection: Maybe<Array<Scalars['String']>>;
};

export type PartitionSetBackfillsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionSetPartitionArgs = {
  partitionName: Scalars['String'];
};

export type PartitionSetPartitionsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  reverse?: InputMaybe<Scalars['Boolean']>;
};

export type PartitionSetNotFoundError = Error & {
  __typename: 'PartitionSetNotFoundError';
  message: Scalars['String'];
  partitionSetName: Scalars['String'];
};

export type PartitionSetOrError = PartitionSet | PartitionSetNotFoundError | PythonError;

export type PartitionSetSelector = {
  partitionSetName: Scalars['String'];
  repositorySelector: RepositorySelector;
};

export type PartitionSets = {
  __typename: 'PartitionSets';
  results: Array<PartitionSet>;
};

export type PartitionSetsOrError = PartitionSets | PipelineNotFoundError | PythonError;

export type PartitionStats = {
  __typename: 'PartitionStats';
  numFailed: Scalars['Int'];
  numMaterialized: Scalars['Int'];
  numPartitions: Scalars['Int'];
};

export type PartitionStatus = {
  __typename: 'PartitionStatus';
  id: Scalars['String'];
  partitionName: Scalars['String'];
  runDuration: Maybe<Scalars['Float']>;
  runId: Maybe<Scalars['String']>;
  runStatus: Maybe<RunStatus>;
};

export type PartitionStatus1D = DefaultPartitions | TimePartitions;

export type PartitionStatusCounts = {
  __typename: 'PartitionStatusCounts';
  count: Scalars['Int'];
  runStatus: RunStatus;
};

export type PartitionStatuses = {
  __typename: 'PartitionStatuses';
  results: Array<PartitionStatus>;
};

export type PartitionStatusesOrError = PartitionStatuses | PythonError;

export type PartitionTags = {
  __typename: 'PartitionTags';
  results: Array<PipelineTag>;
};

export type PartitionTagsOrError = PartitionTags | PythonError;

export type Partitions = {
  __typename: 'Partitions';
  results: Array<Partition>;
};

export type PartitionsOrError = Partitions | PythonError;

export type PathMetadataEntry = MetadataEntry & {
  __typename: 'PathMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  path: Scalars['String'];
};

export type Permission = {
  __typename: 'Permission';
  disabledReason: Maybe<Scalars['String']>;
  permission: Scalars['String'];
  value: Scalars['Boolean'];
};

export type Pipeline = IPipelineSnapshot &
  SolidContainer & {
    __typename: 'Pipeline';
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<DagsterType>;
    description: Maybe<Scalars['String']>;
    graphName: Scalars['String'];
    id: Scalars['ID'];
    isAssetJob: Scalars['Boolean'];
    isJob: Scalars['Boolean'];
    metadataEntries: Array<MetadataEntry>;
    modes: Array<Mode>;
    name: Scalars['String'];
    parentSnapshotId: Maybe<Scalars['String']>;
    pipelineSnapshotId: Scalars['String'];
    presets: Array<PipelinePreset>;
    repository: Repository;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type PipelineDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String'];
};

export type PipelineRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type PipelineSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type PipelineSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type PipelineConfigValidationError = {
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type PipelineConfigValidationInvalid = {
  errors: Array<PipelineConfigValidationError>;
  pipelineName: Scalars['String'];
};

export type PipelineConfigValidationResult =
  | InvalidSubsetError
  | PipelineConfigValidationValid
  | PipelineNotFoundError
  | PythonError
  | RunConfigValidationInvalid;

export type PipelineConfigValidationValid = {
  __typename: 'PipelineConfigValidationValid';
  pipelineName: Scalars['String'];
};

export type PipelineNotFoundError = Error & {
  __typename: 'PipelineNotFoundError';
  message: Scalars['String'];
  pipelineName: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type PipelineOrError = InvalidSubsetError | Pipeline | PipelineNotFoundError | PythonError;

export type PipelinePreset = {
  __typename: 'PipelinePreset';
  mode: Scalars['String'];
  name: Scalars['String'];
  runConfigYaml: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
  tags: Array<PipelineTag>;
};

export type PipelineReference = {
  name: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
};

export type PipelineRun = {
  assets: Array<Asset>;
  canTerminate: Scalars['Boolean'];
  capturedLogs: CapturedLogs;
  computeLogs: ComputeLogs;
  eventConnection: EventConnection;
  executionPlan: Maybe<ExecutionPlan>;
  id: Scalars['ID'];
  jobName: Scalars['String'];
  mode: Scalars['String'];
  parentRunId: Maybe<Scalars['String']>;
  pipeline: PipelineReference;
  pipelineName: Scalars['String'];
  pipelineSnapshotId: Maybe<Scalars['String']>;
  repositoryOrigin: Maybe<RepositoryOrigin>;
  rootRunId: Maybe<Scalars['String']>;
  runConfig: Scalars['RunConfigData'];
  runConfigYaml: Scalars['String'];
  runId: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
  stats: RunStatsSnapshotOrError;
  status: RunStatus;
  stepKeysToExecute: Maybe<Array<Scalars['String']>>;
  stepStats: Array<RunStepStats>;
  tags: Array<PipelineTag>;
};

export type PipelineRunCapturedLogsArgs = {
  fileKey: Scalars['String'];
};

export type PipelineRunComputeLogsArgs = {
  stepKey: Scalars['String'];
};

export type PipelineRunEventConnectionArgs = {
  afterCursor?: InputMaybe<Scalars['String']>;
};

export type PipelineRunConflict = {
  message: Scalars['String'];
};

export type PipelineRunLogsSubscriptionFailure = {
  __typename: 'PipelineRunLogsSubscriptionFailure';
  message: Scalars['String'];
  missingRunId: Maybe<Scalars['String']>;
};

export type PipelineRunLogsSubscriptionPayload =
  | PipelineRunLogsSubscriptionFailure
  | PipelineRunLogsSubscriptionSuccess;

export type PipelineRunLogsSubscriptionSuccess = {
  __typename: 'PipelineRunLogsSubscriptionSuccess';
  cursor: Scalars['String'];
  hasMorePastEvents: Scalars['Boolean'];
  messages: Array<DagsterRunEvent>;
  run: Run;
};

export type PipelineRunMetadataEntry = MetadataEntry & {
  __typename: 'PipelineRunMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  runId: Scalars['String'];
};

export type PipelineRunNotFoundError = {
  message: Scalars['String'];
  runId: Scalars['String'];
};

export type PipelineRunStatsSnapshot = {
  endTime: Maybe<Scalars['Float']>;
  enqueuedTime: Maybe<Scalars['Float']>;
  expectations: Scalars['Int'];
  id: Scalars['String'];
  launchTime: Maybe<Scalars['Float']>;
  materializations: Scalars['Int'];
  runId: Scalars['String'];
  startTime: Maybe<Scalars['Float']>;
  stepsFailed: Scalars['Int'];
  stepsSucceeded: Scalars['Int'];
};

export type PipelineRunStepStats = {
  endTime: Maybe<Scalars['Float']>;
  expectationResults: Array<ExpectationResult>;
  materializations: Array<MaterializationEvent>;
  runId: Scalars['String'];
  startTime: Maybe<Scalars['Float']>;
  status: Maybe<StepEventStatus>;
  stepKey: Scalars['String'];
};

export type PipelineRuns = {
  count: Maybe<Scalars['Int']>;
  results: Array<Run>;
};

export type PipelineSelector = {
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  pipelineName: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  solidSelection?: InputMaybe<Array<Scalars['String']>>;
};

export type PipelineSnapshot = IPipelineSnapshot &
  PipelineReference &
  SolidContainer & {
    __typename: 'PipelineSnapshot';
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<DagsterType>;
    description: Maybe<Scalars['String']>;
    graphName: Scalars['String'];
    id: Scalars['ID'];
    metadataEntries: Array<MetadataEntry>;
    modes: Array<Mode>;
    name: Scalars['String'];
    parentSnapshotId: Maybe<Scalars['String']>;
    pipelineSnapshotId: Scalars['String'];
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solidSelection: Maybe<Array<Scalars['String']>>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type PipelineSnapshotDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String'];
};

export type PipelineSnapshotRunsArgs = {
  cursor?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
};

export type PipelineSnapshotSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type PipelineSnapshotSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type PipelineSnapshotNotFoundError = Error & {
  __typename: 'PipelineSnapshotNotFoundError';
  message: Scalars['String'];
  snapshotId: Scalars['String'];
};

export type PipelineSnapshotOrError =
  | PipelineNotFoundError
  | PipelineSnapshot
  | PipelineSnapshotNotFoundError
  | PythonError;

export type PipelineTag = {
  __typename: 'PipelineTag';
  key: Scalars['String'];
  value: Scalars['String'];
};

export type PipelineTagAndValues = {
  __typename: 'PipelineTagAndValues';
  key: Scalars['String'];
  values: Array<Scalars['String']>;
};

export type PresetNotFoundError = Error & {
  __typename: 'PresetNotFoundError';
  message: Scalars['String'];
  preset: Scalars['String'];
};

export type PythonArtifactMetadataEntry = MetadataEntry & {
  __typename: 'PythonArtifactMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  module: Scalars['String'];
  name: Scalars['String'];
};

export type PythonError = Error & {
  __typename: 'PythonError';
  cause: Maybe<PythonError>;
  causes: Array<PythonError>;
  className: Maybe<Scalars['String']>;
  errorChain: Array<ErrorChainLink>;
  message: Scalars['String'];
  stack: Array<Scalars['String']>;
};

export type ReexecutionParams = {
  parentRunId: Scalars['String'];
  strategy: ReexecutionStrategy;
};

export enum ReexecutionStrategy {
  ALL_STEPS = 'ALL_STEPS',
  FROM_FAILURE = 'FROM_FAILURE',
}

export type RegularConfigType = ConfigType & {
  __typename: 'RegularConfigType';
  description: Maybe<Scalars['String']>;
  givenName: Scalars['String'];
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  typeParamKeys: Array<Scalars['String']>;
};

export type RegularDagsterType = DagsterType & {
  __typename: 'RegularDagsterType';
  description: Maybe<Scalars['String']>;
  displayName: Scalars['String'];
  innerTypes: Array<DagsterType>;
  inputSchemaType: Maybe<ConfigType>;
  isBuiltin: Scalars['Boolean'];
  isList: Scalars['Boolean'];
  isNothing: Scalars['Boolean'];
  isNullable: Scalars['Boolean'];
  key: Scalars['String'];
  metadataEntries: Array<MetadataEntry>;
  name: Maybe<Scalars['String']>;
  outputSchemaType: Maybe<ConfigType>;
};

export type ReloadNotSupported = Error & {
  __typename: 'ReloadNotSupported';
  message: Scalars['String'];
};

export type ReloadRepositoryLocationMutation = {
  __typename: 'ReloadRepositoryLocationMutation';
  Output: ReloadRepositoryLocationMutationResult;
};

export type ReloadRepositoryLocationMutationResult =
  | PythonError
  | ReloadNotSupported
  | RepositoryLocationNotFound
  | UnauthorizedError
  | WorkspaceLocationEntry;

export type ReloadWorkspaceMutation = {
  __typename: 'ReloadWorkspaceMutation';
  Output: ReloadWorkspaceMutationResult;
};

export type ReloadWorkspaceMutationResult = PythonError | UnauthorizedError | Workspace;

export type RepositoriesOrError = PythonError | RepositoryConnection;

export type Repository = {
  __typename: 'Repository';
  allTopLevelResourceDetails: Array<ResourceDetails>;
  assetGroups: Array<AssetGroup>;
  assetNodes: Array<AssetNode>;
  displayMetadata: Array<RepositoryMetadata>;
  id: Scalars['ID'];
  jobs: Array<Job>;
  location: RepositoryLocation;
  name: Scalars['String'];
  origin: RepositoryOrigin;
  partitionSets: Array<PartitionSet>;
  pipelines: Array<Pipeline>;
  schedules: Array<Schedule>;
  sensors: Array<Sensor>;
  usedSolid: Maybe<UsedSolid>;
  usedSolids: Array<UsedSolid>;
};

export type RepositoryUsedSolidArgs = {
  name: Scalars['String'];
};

export type RepositoryConnection = {
  __typename: 'RepositoryConnection';
  nodes: Array<Repository>;
};

export type RepositoryLocation = {
  __typename: 'RepositoryLocation';
  dagsterLibraryVersions: Maybe<Array<DagsterLibraryVersion>>;
  environmentPath: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  isReloadSupported: Scalars['Boolean'];
  name: Scalars['String'];
  repositories: Array<Repository>;
  serverId: Maybe<Scalars['String']>;
};

export enum RepositoryLocationLoadStatus {
  LOADED = 'LOADED',
  LOADING = 'LOADING',
}

export type RepositoryLocationNotFound = Error & {
  __typename: 'RepositoryLocationNotFound';
  message: Scalars['String'];
};

export type RepositoryLocationOrLoadError = PythonError | RepositoryLocation;

export type RepositoryMetadata = {
  __typename: 'RepositoryMetadata';
  key: Scalars['String'];
  value: Scalars['String'];
};

export type RepositoryNotFoundError = Error & {
  __typename: 'RepositoryNotFoundError';
  message: Scalars['String'];
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type RepositoryOrError = PythonError | Repository | RepositoryNotFoundError;

export type RepositoryOrigin = {
  __typename: 'RepositoryOrigin';
  id: Scalars['String'];
  repositoryLocationMetadata: Array<RepositoryMetadata>;
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type RepositorySelector = {
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
};

export type Resource = {
  __typename: 'Resource';
  configField: Maybe<ConfigTypeField>;
  description: Maybe<Scalars['String']>;
  name: Scalars['String'];
};

export type ResourceDetails = {
  __typename: 'ResourceDetails';
  configFields: Array<ConfigTypeField>;
  configuredValues: Array<ConfiguredValue>;
  description: Maybe<Scalars['String']>;
  name: Scalars['String'];
};

export type ResourceDetailsList = {
  __typename: 'ResourceDetailsList';
  results: Array<ResourceDetails>;
};

export type ResourceDetailsOrError = PythonError | ResourceDetails | ResourceNotFoundError;

export type ResourceInitFailureEvent = DisplayableEvent &
  ErrorEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ResourceInitFailureEvent';
    description: Maybe<Scalars['String']>;
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ResourceInitStartedEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ResourceInitStartedEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ResourceInitSuccessEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ResourceInitSuccessEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type ResourceNotFoundError = Error & {
  __typename: 'ResourceNotFoundError';
  message: Scalars['String'];
  resourceName: Scalars['String'];
};

export type ResourceRequirement = {
  __typename: 'ResourceRequirement';
  resourceKey: Scalars['String'];
};

export type ResourceSelector = {
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  resourceName: Scalars['String'];
};

export type ResourcesOrError = PythonError | RepositoryNotFoundError | ResourceDetailsList;

export type ResumeBackfillResult = PythonError | ResumeBackfillSuccess | UnauthorizedError;

export type ResumeBackfillSuccess = {
  __typename: 'ResumeBackfillSuccess';
  backfillId: Scalars['String'];
};

export type Run = PipelineRun & {
  __typename: 'Run';
  assetMaterializations: Array<MaterializationEvent>;
  assetSelection: Maybe<Array<AssetKey>>;
  assets: Array<Asset>;
  canTerminate: Scalars['Boolean'];
  capturedLogs: CapturedLogs;
  computeLogs: ComputeLogs;
  endTime: Maybe<Scalars['Float']>;
  eventConnection: EventConnection;
  executionPlan: Maybe<ExecutionPlan>;
  hasDeletePermission: Scalars['Boolean'];
  hasReExecutePermission: Scalars['Boolean'];
  hasTerminatePermission: Scalars['Boolean'];
  id: Scalars['ID'];
  jobName: Scalars['String'];
  mode: Scalars['String'];
  parentPipelineSnapshotId: Maybe<Scalars['String']>;
  parentRunId: Maybe<Scalars['String']>;
  pipeline: PipelineReference;
  pipelineName: Scalars['String'];
  pipelineSnapshotId: Maybe<Scalars['String']>;
  repositoryOrigin: Maybe<RepositoryOrigin>;
  resolvedOpSelection: Maybe<Array<Scalars['String']>>;
  rootRunId: Maybe<Scalars['String']>;
  runConfig: Scalars['RunConfigData'];
  runConfigYaml: Scalars['String'];
  runId: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
  startTime: Maybe<Scalars['Float']>;
  stats: RunStatsSnapshotOrError;
  status: RunStatus;
  stepKeysToExecute: Maybe<Array<Scalars['String']>>;
  stepStats: Array<RunStepStats>;
  tags: Array<PipelineTag>;
  updateTime: Maybe<Scalars['Float']>;
};

export type RunCapturedLogsArgs = {
  fileKey: Scalars['String'];
};

export type RunComputeLogsArgs = {
  stepKey: Scalars['String'];
};

export type RunEventConnectionArgs = {
  afterCursor?: InputMaybe<Scalars['String']>;
};

export type RunCanceledEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunCanceledEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunCancelingEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunCancelingEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunConfigSchema = {
  __typename: 'RunConfigSchema';
  allConfigTypes: Array<ConfigType>;
  isRunConfigValid: PipelineConfigValidationResult;
  rootConfigType: ConfigType;
};

export type RunConfigSchemaIsRunConfigValidArgs = {
  runConfigData?: InputMaybe<Scalars['RunConfigData']>;
};

export type RunConfigSchemaOrError =
  | InvalidSubsetError
  | ModeNotFoundError
  | PipelineNotFoundError
  | PythonError
  | RunConfigSchema;

export type RunConfigValidationInvalid = PipelineConfigValidationInvalid & {
  __typename: 'RunConfigValidationInvalid';
  errors: Array<PipelineConfigValidationError>;
  pipelineName: Scalars['String'];
};

export type RunConflict = Error &
  PipelineRunConflict & {
    __typename: 'RunConflict';
    message: Scalars['String'];
  };

export type RunDequeuedEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunDequeuedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunEnqueuedEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunEnqueuedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunEvent = {
  pipelineName: Scalars['String'];
};

export type RunFailureEvent = ErrorEvent &
  MessageEvent &
  RunEvent & {
    __typename: 'RunFailureEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunGroup = {
  __typename: 'RunGroup';
  rootRunId: Scalars['String'];
  runs: Maybe<Array<Maybe<Run>>>;
};

export type RunGroupNotFoundError = Error & {
  __typename: 'RunGroupNotFoundError';
  message: Scalars['String'];
  runId: Scalars['String'];
};

export type RunGroupOrError = PythonError | RunGroup | RunGroupNotFoundError;

export type RunGroups = {
  __typename: 'RunGroups';
  results: Array<RunGroup>;
};

export type RunGroupsOrError = {
  __typename: 'RunGroupsOrError';
  results: Array<RunGroup>;
};

export type RunLauncher = {
  __typename: 'RunLauncher';
  name: Scalars['String'];
};

export type RunMarker = {
  __typename: 'RunMarker';
  endTime: Maybe<Scalars['Float']>;
  startTime: Maybe<Scalars['Float']>;
};

export type RunNotFoundError = Error &
  PipelineRunNotFoundError & {
    __typename: 'RunNotFoundError';
    message: Scalars['String'];
    runId: Scalars['String'];
  };

export type RunOrError = PythonError | Run | RunNotFoundError;

export type RunRequest = {
  __typename: 'RunRequest';
  runConfigYaml: Scalars['String'];
  runKey: Maybe<Scalars['String']>;
  tags: Array<PipelineTag>;
};

export type RunStartEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunStartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunStartingEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunStartingEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunStatsSnapshot = PipelineRunStatsSnapshot & {
  __typename: 'RunStatsSnapshot';
  endTime: Maybe<Scalars['Float']>;
  enqueuedTime: Maybe<Scalars['Float']>;
  expectations: Scalars['Int'];
  id: Scalars['String'];
  launchTime: Maybe<Scalars['Float']>;
  materializations: Scalars['Int'];
  runId: Scalars['String'];
  startTime: Maybe<Scalars['Float']>;
  stepsFailed: Scalars['Int'];
  stepsSucceeded: Scalars['Int'];
};

export type RunStatsSnapshotOrError = PythonError | RunStatsSnapshot;

export enum RunStatus {
  CANCELED = 'CANCELED',
  CANCELING = 'CANCELING',
  FAILURE = 'FAILURE',
  MANAGED = 'MANAGED',
  NOT_STARTED = 'NOT_STARTED',
  QUEUED = 'QUEUED',
  STARTED = 'STARTED',
  STARTING = 'STARTING',
  SUCCESS = 'SUCCESS',
}

export type RunStepStats = PipelineRunStepStats & {
  __typename: 'RunStepStats';
  attempts: Array<RunMarker>;
  endTime: Maybe<Scalars['Float']>;
  expectationResults: Array<ExpectationResult>;
  markers: Array<RunMarker>;
  materializations: Array<MaterializationEvent>;
  runId: Scalars['String'];
  startTime: Maybe<Scalars['Float']>;
  status: Maybe<StepEventStatus>;
  stepKey: Scalars['String'];
};

export type RunSuccessEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunSuccessEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String'];
    pipelineName: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type RunTagKeys = {
  __typename: 'RunTagKeys';
  keys: Array<Scalars['String']>;
};

export type RunTagKeysOrError = PythonError | RunTagKeys;

export type RunTags = {
  __typename: 'RunTags';
  tags: Array<PipelineTagAndValues>;
};

export type RunTagsOrError = PythonError | RunTags;

export type Runs = PipelineRuns & {
  __typename: 'Runs';
  count: Maybe<Scalars['Int']>;
  results: Array<Run>;
};

export type RunsFilter = {
  createdBefore?: InputMaybe<Scalars['Float']>;
  mode?: InputMaybe<Scalars['String']>;
  pipelineName?: InputMaybe<Scalars['String']>;
  runIds?: InputMaybe<Array<InputMaybe<Scalars['String']>>>;
  snapshotId?: InputMaybe<Scalars['String']>;
  statuses?: InputMaybe<Array<RunStatus>>;
  tags?: InputMaybe<Array<ExecutionTag>>;
  updatedAfter?: InputMaybe<Scalars['Float']>;
};

export type RunsOrError = InvalidPipelineRunsFilterError | PythonError | Runs;

export type RuntimeMismatchConfigError = PipelineConfigValidationError & {
  __typename: 'RuntimeMismatchConfigError';
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
  valueRep: Maybe<Scalars['String']>;
};

export type ScalarUnionConfigType = ConfigType & {
  __typename: 'ScalarUnionConfigType';
  description: Maybe<Scalars['String']>;
  isSelector: Scalars['Boolean'];
  key: Scalars['String'];
  nonScalarType: ConfigType;
  nonScalarTypeKey: Scalars['String'];
  recursiveConfigTypes: Array<ConfigType>;
  scalarType: ConfigType;
  scalarTypeKey: Scalars['String'];
  typeParamKeys: Array<Scalars['String']>;
};

export type Schedule = {
  __typename: 'Schedule';
  cronSchedule: Scalars['String'];
  description: Maybe<Scalars['String']>;
  executionTimezone: Maybe<Scalars['String']>;
  futureTick: DryRunInstigationTick;
  futureTicks: DryRunInstigationTicks;
  id: Scalars['ID'];
  mode: Scalars['String'];
  name: Scalars['String'];
  partitionSet: Maybe<PartitionSet>;
  pipelineName: Scalars['String'];
  potentialTickTimestamps: Array<Scalars['Float']>;
  scheduleState: InstigationState;
  solidSelection: Maybe<Array<Maybe<Scalars['String']>>>;
};

export type ScheduleFutureTickArgs = {
  tickTimestamp: Scalars['Int'];
};

export type ScheduleFutureTicksArgs = {
  cursor?: InputMaybe<Scalars['Float']>;
  limit?: InputMaybe<Scalars['Int']>;
  until?: InputMaybe<Scalars['Float']>;
};

export type SchedulePotentialTickTimestampsArgs = {
  lowerLimit?: InputMaybe<Scalars['Int']>;
  startTimestamp?: InputMaybe<Scalars['Float']>;
  upperLimit?: InputMaybe<Scalars['Int']>;
};

export type ScheduleData = {
  __typename: 'ScheduleData';
  cronSchedule: Scalars['String'];
  startTimestamp: Maybe<Scalars['Float']>;
};

export type ScheduleDryRunResult = DryRunInstigationTick | PythonError | ScheduleNotFoundError;

export type ScheduleMutationResult = PythonError | ScheduleStateResult | UnauthorizedError;

export type ScheduleNotFoundError = Error & {
  __typename: 'ScheduleNotFoundError';
  message: Scalars['String'];
  scheduleName: Scalars['String'];
};

export type ScheduleOrError = PythonError | Schedule | ScheduleNotFoundError;

export type ScheduleSelector = {
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  scheduleName: Scalars['String'];
};

export type ScheduleStateResult = {
  __typename: 'ScheduleStateResult';
  scheduleState: InstigationState;
};

export enum ScheduleStatus {
  ENDED = 'ENDED',
  RUNNING = 'RUNNING',
  STOPPED = 'STOPPED',
}

export type ScheduleTick = {
  __typename: 'ScheduleTick';
  status: InstigationTickStatus;
  tickId: Scalars['String'];
  tickSpecificData: Maybe<ScheduleTickSpecificData>;
  timestamp: Scalars['Float'];
};

export type ScheduleTickFailureData = {
  __typename: 'ScheduleTickFailureData';
  error: PythonError;
};

export type ScheduleTickSpecificData = ScheduleTickFailureData | ScheduleTickSuccessData;

export type ScheduleTickSuccessData = {
  __typename: 'ScheduleTickSuccessData';
  run: Maybe<Run>;
};

export type Scheduler = {
  __typename: 'Scheduler';
  schedulerClass: Maybe<Scalars['String']>;
};

export type SchedulerNotDefinedError = Error & {
  __typename: 'SchedulerNotDefinedError';
  message: Scalars['String'];
};

export type SchedulerOrError = PythonError | Scheduler | SchedulerNotDefinedError;

export type Schedules = {
  __typename: 'Schedules';
  results: Array<Schedule>;
};

export type SchedulesOrError = PythonError | RepositoryNotFoundError | Schedules;

export type SelectorTypeConfigError = PipelineConfigValidationError & {
  __typename: 'SelectorTypeConfigError';
  incomingFields: Array<Scalars['String']>;
  message: Scalars['String'];
  path: Array<Scalars['String']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type Sensor = {
  __typename: 'Sensor';
  description: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  jobOriginId: Scalars['String'];
  metadata: SensorMetadata;
  minIntervalSeconds: Scalars['Int'];
  name: Scalars['String'];
  nextTick: Maybe<DryRunInstigationTick>;
  sensorState: InstigationState;
  sensorType: SensorType;
  targets: Maybe<Array<Target>>;
};

export type SensorData = {
  __typename: 'SensorData';
  lastCursor: Maybe<Scalars['String']>;
  lastRunKey: Maybe<Scalars['String']>;
  lastTickTimestamp: Maybe<Scalars['Float']>;
};

export type SensorDryRunResult = DryRunInstigationTick | PythonError | SensorNotFoundError;

export type SensorMetadata = {
  __typename: 'SensorMetadata';
  assetKeys: Maybe<Array<AssetKey>>;
};

export type SensorNotFoundError = Error & {
  __typename: 'SensorNotFoundError';
  message: Scalars['String'];
  sensorName: Scalars['String'];
};

export type SensorOrError = PythonError | Sensor | SensorNotFoundError | UnauthorizedError;

export type SensorSelector = {
  repositoryLocationName: Scalars['String'];
  repositoryName: Scalars['String'];
  sensorName: Scalars['String'];
};

export enum SensorType {
  ASSET = 'ASSET',
  FRESHNESS_POLICY = 'FRESHNESS_POLICY',
  MULTI_ASSET = 'MULTI_ASSET',
  RUN_STATUS = 'RUN_STATUS',
  STANDARD = 'STANDARD',
  UNKNOWN = 'UNKNOWN',
}

export type Sensors = {
  __typename: 'Sensors';
  results: Array<Sensor>;
};

export type SensorsOrError = PythonError | RepositoryNotFoundError | Sensors;

export type SetSensorCursorMutation = {
  __typename: 'SetSensorCursorMutation';
  Output: SensorOrError;
};

export type ShutdownRepositoryLocationMutation = {
  __typename: 'ShutdownRepositoryLocationMutation';
  Output: ShutdownRepositoryLocationMutationResult;
};

export type ShutdownRepositoryLocationMutationResult =
  | PythonError
  | RepositoryLocationNotFound
  | ShutdownRepositoryLocationSuccess
  | UnauthorizedError;

export type ShutdownRepositoryLocationSuccess = {
  __typename: 'ShutdownRepositoryLocationSuccess';
  repositoryLocationName: Scalars['String'];
};

export type Solid = {
  __typename: 'Solid';
  definition: ISolidDefinition;
  inputs: Array<Input>;
  isDynamicMapped: Scalars['Boolean'];
  name: Scalars['String'];
  outputs: Array<Output>;
};

export type SolidContainer = {
  description: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  modes: Array<Mode>;
  name: Scalars['String'];
  solidHandle: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
};

export type SolidContainerSolidHandleArgs = {
  handleID: Scalars['String'];
};

export type SolidContainerSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']>;
};

export type SolidDefinition = ISolidDefinition & {
  __typename: 'SolidDefinition';
  assetNodes: Array<AssetNode>;
  configField: Maybe<ConfigTypeField>;
  description: Maybe<Scalars['String']>;
  inputDefinitions: Array<InputDefinition>;
  metadata: Array<MetadataItemDefinition>;
  name: Scalars['String'];
  outputDefinitions: Array<OutputDefinition>;
  requiredResources: Array<ResourceRequirement>;
};

export type SolidHandle = {
  __typename: 'SolidHandle';
  handleID: Scalars['String'];
  parent: Maybe<SolidHandle>;
  solid: Solid;
  stepStats: Maybe<SolidStepStatsOrError>;
};

export type SolidHandleStepStatsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type SolidStepStatsConnection = {
  __typename: 'SolidStepStatsConnection';
  nodes: Array<RunStepStats>;
};

export type SolidStepStatsOrError = SolidStepStatsConnection | SolidStepStatusUnavailableError;

export type SolidStepStatusUnavailableError = Error & {
  __typename: 'SolidStepStatusUnavailableError';
  message: Scalars['String'];
};

export type StaleCause = {
  __typename: 'StaleCause';
  dependency: Maybe<AssetKey>;
  key: AssetKey;
  reason: Scalars['String'];
};

export enum StaleStatus {
  FRESH = 'FRESH',
  MISSING = 'MISSING',
  STALE = 'STALE',
}

export type StartScheduleMutation = {
  __typename: 'StartScheduleMutation';
  Output: ScheduleMutationResult;
};

export type StepEvent = {
  solidHandleID: Maybe<Scalars['String']>;
  stepKey: Maybe<Scalars['String']>;
};

export enum StepEventStatus {
  FAILURE = 'FAILURE',
  IN_PROGRESS = 'IN_PROGRESS',
  SKIPPED = 'SKIPPED',
  SUCCESS = 'SUCCESS',
}

export type StepExecution = {
  marshalledInputs?: InputMaybe<Array<MarshalledInput>>;
  marshalledOutputs?: InputMaybe<Array<MarshalledOutput>>;
  stepKey: Scalars['String'];
};

export type StepExpectationResultEvent = MessageEvent &
  StepEvent & {
    __typename: 'StepExpectationResultEvent';
    eventType: Maybe<DagsterEventType>;
    expectationResult: ExpectationResult;
    level: LogLevel;
    message: Scalars['String'];
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export enum StepKind {
  COMPUTE = 'COMPUTE',
  UNRESOLVED_COLLECT = 'UNRESOLVED_COLLECT',
  UNRESOLVED_MAPPED = 'UNRESOLVED_MAPPED',
}

export type StepOutputHandle = {
  outputName: Scalars['String'];
  stepKey: Scalars['String'];
};

export type StepWorkerStartedEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'StepWorkerStartedEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type StepWorkerStartingEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'StepWorkerStartingEvent';
    description: Maybe<Scalars['String']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']>;
    markerStart: Maybe<Scalars['String']>;
    message: Scalars['String'];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars['String'];
    solidHandleID: Maybe<Scalars['String']>;
    stepKey: Maybe<Scalars['String']>;
    timestamp: Scalars['String'];
  };

export type StopRunningScheduleMutation = {
  __typename: 'StopRunningScheduleMutation';
  Output: ScheduleMutationResult;
};

export type StopSensorMutation = {
  __typename: 'StopSensorMutation';
  Output: StopSensorMutationResultOrError;
};

export type StopSensorMutationResult = {
  __typename: 'StopSensorMutationResult';
  instigationState: Maybe<InstigationState>;
};

export type StopSensorMutationResultOrError =
  | PythonError
  | StopSensorMutationResult
  | UnauthorizedError;

export type Table = {
  __typename: 'Table';
  records: Array<Scalars['String']>;
  schema: TableSchema;
};

export type TableColumn = {
  __typename: 'TableColumn';
  constraints: TableColumnConstraints;
  description: Maybe<Scalars['String']>;
  name: Scalars['String'];
  type: Scalars['String'];
};

export type TableColumnConstraints = {
  __typename: 'TableColumnConstraints';
  nullable: Scalars['Boolean'];
  other: Array<Scalars['String']>;
  unique: Scalars['Boolean'];
};

export type TableConstraints = {
  __typename: 'TableConstraints';
  other: Array<Scalars['String']>;
};

export type TableMetadataEntry = MetadataEntry & {
  __typename: 'TableMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  table: Table;
};

export type TableSchema = {
  __typename: 'TableSchema';
  columns: Array<TableColumn>;
  constraints: Maybe<TableConstraints>;
};

export type TableSchemaMetadataEntry = MetadataEntry & {
  __typename: 'TableSchemaMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  schema: TableSchema;
};

export type Target = {
  __typename: 'Target';
  mode: Scalars['String'];
  pipelineName: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
};

export type TerminatePipelineExecutionFailure = {
  message: Scalars['String'];
  run: Run;
};

export type TerminatePipelineExecutionSuccess = {
  run: Run;
};

export type TerminateRunFailure = TerminatePipelineExecutionFailure & {
  __typename: 'TerminateRunFailure';
  message: Scalars['String'];
  run: Run;
};

export type TerminateRunMutation = {
  __typename: 'TerminateRunMutation';
  Output: TerminateRunResult;
};

export enum TerminateRunPolicy {
  MARK_AS_CANCELED_IMMEDIATELY = 'MARK_AS_CANCELED_IMMEDIATELY',
  SAFE_TERMINATE = 'SAFE_TERMINATE',
}

export type TerminateRunResult =
  | PythonError
  | RunNotFoundError
  | TerminateRunFailure
  | TerminateRunSuccess
  | UnauthorizedError;

export type TerminateRunSuccess = TerminatePipelineExecutionSuccess & {
  __typename: 'TerminateRunSuccess';
  run: Run;
};

export type TestFields = {
  __typename: 'TestFields';
  alwaysException: Maybe<Scalars['String']>;
};

export type TextMetadataEntry = MetadataEntry & {
  __typename: 'TextMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  text: Scalars['String'];
};

export type TickEvaluation = {
  __typename: 'TickEvaluation';
  cursor: Maybe<Scalars['String']>;
  error: Maybe<PythonError>;
  runRequests: Maybe<Array<RunRequest>>;
  skipReason: Maybe<Scalars['String']>;
};

export type TimePartitionRange = {
  __typename: 'TimePartitionRange';
  endKey: Scalars['String'];
  endTime: Scalars['Float'];
  startKey: Scalars['String'];
  startTime: Scalars['Float'];
  status: PartitionRangeStatus;
};

export type TimePartitions = {
  __typename: 'TimePartitions';
  ranges: Array<TimePartitionRange>;
};

export type TimePartitionsDefinitionMetadata = {
  __typename: 'TimePartitionsDefinitionMetadata';
  endKey: Scalars['String'];
  endTime: Scalars['Float'];
  startKey: Scalars['String'];
  startTime: Scalars['Float'];
};

export type TypeCheck = DisplayableEvent & {
  __typename: 'TypeCheck';
  description: Maybe<Scalars['String']>;
  label: Maybe<Scalars['String']>;
  metadataEntries: Array<MetadataEntry>;
  success: Scalars['Boolean'];
};

export type UnauthorizedError = Error & {
  __typename: 'UnauthorizedError';
  message: Scalars['String'];
};

export type UnknownPipeline = PipelineReference & {
  __typename: 'UnknownPipeline';
  name: Scalars['String'];
  solidSelection: Maybe<Array<Scalars['String']>>;
};

export type UrlMetadataEntry = MetadataEntry & {
  __typename: 'UrlMetadataEntry';
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
  url: Scalars['String'];
};

export type UsedSolid = {
  __typename: 'UsedSolid';
  definition: ISolidDefinition;
  invocations: Array<NodeInvocationSite>;
};

export type Workspace = {
  __typename: 'Workspace';
  locationEntries: Array<WorkspaceLocationEntry>;
};

export type WorkspaceLocationEntry = {
  __typename: 'WorkspaceLocationEntry';
  displayMetadata: Array<RepositoryMetadata>;
  id: Scalars['ID'];
  loadStatus: RepositoryLocationLoadStatus;
  locationOrLoadError: Maybe<RepositoryLocationOrLoadError>;
  name: Scalars['String'];
  permissions: Array<Permission>;
  updatedTimestamp: Scalars['Float'];
};

export type WorkspaceLocationStatusEntries = {
  __typename: 'WorkspaceLocationStatusEntries';
  entries: Array<WorkspaceLocationStatusEntry>;
};

export type WorkspaceLocationStatusEntriesOrError = PythonError | WorkspaceLocationStatusEntries;

export type WorkspaceLocationStatusEntry = {
  __typename: 'WorkspaceLocationStatusEntry';
  id: Scalars['ID'];
  loadStatus: RepositoryLocationLoadStatus;
  name: Scalars['String'];
  updateTimestamp: Scalars['Float'];
};

export type WorkspaceOrError = PythonError | Workspace;

export type WrappingConfigType = {
  ofType: ConfigType;
};

export type WrappingDagsterType = {
  ofType: DagsterType;
};

export const buildAddDynamicPartitionSuccess = (
  overrides?: Partial<Types.AddDynamicPartitionSuccess>,
): {__typename: 'AddDynamicPartitionSuccess'} & Types.AddDynamicPartitionSuccess => {
  return {
    __typename: 'AddDynamicPartitionSuccess',
    partitionKey:
      overrides && overrides.hasOwnProperty('partitionKey') ? overrides.partitionKey! : 'deleniti',
    partitionsDefName:
      overrides && overrides.hasOwnProperty('partitionsDefName')
        ? overrides.partitionsDefName!
        : 'voluptates',
  };
};

export const buildAlertFailureEvent = (
  overrides?: Partial<Types.AlertFailureEvent>,
): {__typename: 'AlertFailureEvent'} & Types.AlertFailureEvent => {
  return {
    __typename: 'AlertFailureEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quia',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'odio',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'excepturi',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'et',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'suscipit',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'eos',
  };
};

export const buildAlertStartEvent = (
  overrides?: Partial<Types.AlertStartEvent>,
): {__typename: 'AlertStartEvent'} & Types.AlertStartEvent => {
  return {
    __typename: 'AlertStartEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'in',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'repellendus',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'quae',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'enim',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'deserunt',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'illum',
  };
};

export const buildAlertSuccessEvent = (
  overrides?: Partial<Types.AlertSuccessEvent>,
): {__typename: 'AlertSuccessEvent'} & Types.AlertSuccessEvent => {
  return {
    __typename: 'AlertSuccessEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quia',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'labore',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'rem',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'at',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'veritatis',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'quia',
  };
};

export const buildArrayConfigType = (
  overrides?: Partial<Types.ArrayConfigType>,
): {__typename: 'ArrayConfigType'} & Types.ArrayConfigType => {
  return {
    __typename: 'ArrayConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'aliquam',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'omnis',
    ofType: overrides && overrides.hasOwnProperty('ofType') ? overrides.ofType! : buildConfigType(),
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [buildConfigType(), buildConfigType(), buildConfigType()],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys')
        ? overrides.typeParamKeys!
        : ['delectus', 'ea', 'architecto'],
  };
};

export const buildAsset = (
  overrides?: Partial<Types.Asset>,
): {__typename: 'Asset'} & Types.Asset => {
  return {
    __typename: 'Asset',
    assetMaterializations:
      overrides && overrides.hasOwnProperty('assetMaterializations')
        ? overrides.assetMaterializations!
        : [buildMaterializationEvent(), buildMaterializationEvent(), buildMaterializationEvent()],
    assetObservations:
      overrides && overrides.hasOwnProperty('assetObservations')
        ? overrides.assetObservations!
        : [buildObservationEvent(), buildObservationEvent(), buildObservationEvent()],
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : buildAssetNode(),
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'omnis',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : buildAssetKey(),
  };
};

export const buildAssetConnection = (
  overrides?: Partial<Types.AssetConnection>,
): {__typename: 'AssetConnection'} & Types.AssetConnection => {
  return {
    __typename: 'AssetConnection',
    nodes:
      overrides && overrides.hasOwnProperty('nodes')
        ? overrides.nodes!
        : [buildAsset(), buildAsset(), buildAsset()],
  };
};

export const buildAssetDependency = (
  overrides?: Partial<Types.AssetDependency>,
): {__typename: 'AssetDependency'} & Types.AssetDependency => {
  return {
    __typename: 'AssetDependency',
    asset: overrides && overrides.hasOwnProperty('asset') ? overrides.asset! : buildAssetNode(),
    inputName:
      overrides && overrides.hasOwnProperty('inputName') ? overrides.inputName! : 'aspernatur',
  };
};

export const buildAssetFreshnessInfo = (
  overrides?: Partial<Types.AssetFreshnessInfo>,
): {__typename: 'AssetFreshnessInfo'} & Types.AssetFreshnessInfo => {
  return {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate:
      overrides && overrides.hasOwnProperty('currentMinutesLate')
        ? overrides.currentMinutesLate!
        : 0.26,
    latestMaterializationMinutesLate:
      overrides && overrides.hasOwnProperty('latestMaterializationMinutesLate')
        ? overrides.latestMaterializationMinutesLate!
        : 7.24,
  };
};

export const buildAssetGroup = (
  overrides?: Partial<Types.AssetGroup>,
): {__typename: 'AssetGroup'} & Types.AssetGroup => {
  return {
    __typename: 'AssetGroup',
    assetKeys:
      overrides && overrides.hasOwnProperty('assetKeys')
        ? overrides.assetKeys!
        : [buildAssetKey(), buildAssetKey(), buildAssetKey()],
    groupName: overrides && overrides.hasOwnProperty('groupName') ? overrides.groupName! : 'aut',
  };
};

export const buildAssetGroupSelector = (
  overrides?: Partial<Types.AssetGroupSelector>,
): Types.AssetGroupSelector => {
  return {
    groupName:
      overrides && overrides.hasOwnProperty('groupName') ? overrides.groupName! : 'explicabo',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'fuga',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'vel',
  };
};

export const buildAssetKey = (
  overrides?: Partial<Types.AssetKey>,
): {__typename: 'AssetKey'} & Types.AssetKey => {
  return {
    __typename: 'AssetKey',
    path:
      overrides && overrides.hasOwnProperty('path')
        ? overrides.path!
        : ['adipisci', 'praesentium', 'voluptatem'],
  };
};

export const buildAssetKeyInput = (
  overrides?: Partial<Types.AssetKeyInput>,
): Types.AssetKeyInput => {
  return {
    path:
      overrides && overrides.hasOwnProperty('path')
        ? overrides.path!
        : ['est', 'perspiciatis', 'ut'],
  };
};

export const buildAssetLatestInfo = (
  overrides?: Partial<Types.AssetLatestInfo>,
): {__typename: 'AssetLatestInfo'} & Types.AssetLatestInfo => {
  return {
    __typename: 'AssetLatestInfo',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey') ? overrides.assetKey! : buildAssetKey(),
    inProgressRunIds:
      overrides && overrides.hasOwnProperty('inProgressRunIds')
        ? overrides.inProgressRunIds!
        : ['impedit', 'ea', 'iure'],
    latestMaterialization:
      overrides && overrides.hasOwnProperty('latestMaterialization')
        ? overrides.latestMaterialization!
        : buildMaterializationEvent(),
    latestRun:
      overrides && overrides.hasOwnProperty('latestRun') ? overrides.latestRun! : buildRun(),
    unstartedRunIds:
      overrides && overrides.hasOwnProperty('unstartedRunIds')
        ? overrides.unstartedRunIds!
        : ['assumenda', 'molestiae', 'sit'],
  };
};

export const buildAssetLineageInfo = (
  overrides?: Partial<Types.AssetLineageInfo>,
): {__typename: 'AssetLineageInfo'} & Types.AssetLineageInfo => {
  return {
    __typename: 'AssetLineageInfo',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey') ? overrides.assetKey! : buildAssetKey(),
    partitions:
      overrides && overrides.hasOwnProperty('partitions')
        ? overrides.partitions!
        : ['et', 'est', 'veniam'],
  };
};

export const buildAssetMaterializationPlannedEvent = (
  overrides?: Partial<Types.AssetMaterializationPlannedEvent>,
): {__typename: 'AssetMaterializationPlannedEvent'} & Types.AssetMaterializationPlannedEvent => {
  return {
    __typename: 'AssetMaterializationPlannedEvent',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey') ? overrides.assetKey! : buildAssetKey(),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'amet',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'nesciunt',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'voluptas',
    runOrError:
      overrides && overrides.hasOwnProperty('runOrError')
        ? overrides.runOrError!
        : buildPythonError(),
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'dolor',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'nulla',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'est',
  };
};

export const buildAssetMetadataEntry = (
  overrides?: Partial<Types.AssetMetadataEntry>,
): {__typename: 'AssetMetadataEntry'} & Types.AssetMetadataEntry => {
  return {
    __typename: 'AssetMetadataEntry',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey') ? overrides.assetKey! : buildAssetKey(),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quasi',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'iste',
  };
};

export const buildAssetNode = (
  overrides?: Partial<Types.AssetNode>,
): {__typename: 'AssetNode'} & Types.AssetNode => {
  return {
    __typename: 'AssetNode',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey') ? overrides.assetKey! : buildAssetKey(),
    assetMaterializationUsedData:
      overrides && overrides.hasOwnProperty('assetMaterializationUsedData')
        ? overrides.assetMaterializationUsedData!
        : [
            buildMaterializationUpstreamDataVersion(),
            buildMaterializationUpstreamDataVersion(),
            buildMaterializationUpstreamDataVersion(),
          ],
    assetMaterializations:
      overrides && overrides.hasOwnProperty('assetMaterializations')
        ? overrides.assetMaterializations!
        : [buildMaterializationEvent(), buildMaterializationEvent(), buildMaterializationEvent()],
    assetObservations:
      overrides && overrides.hasOwnProperty('assetObservations')
        ? overrides.assetObservations!
        : [buildObservationEvent(), buildObservationEvent(), buildObservationEvent()],
    assetPartitionStatuses:
      overrides && overrides.hasOwnProperty('assetPartitionStatuses')
        ? overrides.assetPartitionStatuses!
        : buildDefaultPartitions(),
    computeKind:
      overrides && overrides.hasOwnProperty('computeKind') ? overrides.computeKind! : 'quasi',
    configField:
      overrides && overrides.hasOwnProperty('configField')
        ? overrides.configField!
        : buildConfigTypeField(),
    currentDataVersion:
      overrides && overrides.hasOwnProperty('currentDataVersion')
        ? overrides.currentDataVersion!
        : 'aperiam',
    dependedBy:
      overrides && overrides.hasOwnProperty('dependedBy')
        ? overrides.dependedBy!
        : [buildAssetDependency(), buildAssetDependency(), buildAssetDependency()],
    dependedByKeys:
      overrides && overrides.hasOwnProperty('dependedByKeys')
        ? overrides.dependedByKeys!
        : [buildAssetKey(), buildAssetKey(), buildAssetKey()],
    dependencies:
      overrides && overrides.hasOwnProperty('dependencies')
        ? overrides.dependencies!
        : [buildAssetDependency(), buildAssetDependency(), buildAssetDependency()],
    dependencyKeys:
      overrides && overrides.hasOwnProperty('dependencyKeys')
        ? overrides.dependencyKeys!
        : [buildAssetKey(), buildAssetKey(), buildAssetKey()],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'vitae',
    freshnessInfo:
      overrides && overrides.hasOwnProperty('freshnessInfo')
        ? overrides.freshnessInfo!
        : buildAssetFreshnessInfo(),
    freshnessPolicy:
      overrides && overrides.hasOwnProperty('freshnessPolicy')
        ? overrides.freshnessPolicy!
        : buildFreshnessPolicy(),
    graphName: overrides && overrides.hasOwnProperty('graphName') ? overrides.graphName! : 'et',
    groupName:
      overrides && overrides.hasOwnProperty('groupName') ? overrides.groupName! : 'asperiores',
    hasMaterializePermission:
      overrides && overrides.hasOwnProperty('hasMaterializePermission')
        ? overrides.hasMaterializePermission!
        : false,
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '006fc1b6-3c6e-432d-ac6a-c1c16c0c05b9',
    isObservable:
      overrides && overrides.hasOwnProperty('isObservable') ? overrides.isObservable! : false,
    isPartitioned:
      overrides && overrides.hasOwnProperty('isPartitioned') ? overrides.isPartitioned! : true,
    isSource: overrides && overrides.hasOwnProperty('isSource') ? overrides.isSource! : false,
    jobNames:
      overrides && overrides.hasOwnProperty('jobNames')
        ? overrides.jobNames!
        : ['molestias', 'soluta', 'autem'],
    jobs:
      overrides && overrides.hasOwnProperty('jobs')
        ? overrides.jobs!
        : [buildPipeline(), buildPipeline(), buildPipeline()],
    latestMaterializationByPartition:
      overrides && overrides.hasOwnProperty('latestMaterializationByPartition')
        ? overrides.latestMaterializationByPartition!
        : [buildMaterializationEvent(), buildMaterializationEvent(), buildMaterializationEvent()],
    latestRunForPartition:
      overrides && overrides.hasOwnProperty('latestRunForPartition')
        ? overrides.latestRunForPartition!
        : buildRun(),
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    op: overrides && overrides.hasOwnProperty('op') ? overrides.op! : buildSolidDefinition(),
    opName: overrides && overrides.hasOwnProperty('opName') ? overrides.opName! : 'veritatis',
    opNames:
      overrides && overrides.hasOwnProperty('opNames')
        ? overrides.opNames!
        : ['itaque', 'consequatur', 'voluptatem'],
    opVersion:
      overrides && overrides.hasOwnProperty('opVersion') ? overrides.opVersion! : 'cupiditate',
    partitionDefinition:
      overrides && overrides.hasOwnProperty('partitionDefinition')
        ? overrides.partitionDefinition!
        : buildPartitionDefinition(),
    partitionKeys:
      overrides && overrides.hasOwnProperty('partitionKeys')
        ? overrides.partitionKeys!
        : ['minima', 'nihil', 'mollitia'],
    partitionKeysByDimension:
      overrides && overrides.hasOwnProperty('partitionKeysByDimension')
        ? overrides.partitionKeysByDimension!
        : [
            buildDimensionPartitionKeys(),
            buildDimensionPartitionKeys(),
            buildDimensionPartitionKeys(),
          ],
    partitionStats:
      overrides && overrides.hasOwnProperty('partitionStats')
        ? overrides.partitionStats!
        : buildPartitionStats(),
    repository:
      overrides && overrides.hasOwnProperty('repository')
        ? overrides.repository!
        : buildRepository(),
    requiredResources:
      overrides && overrides.hasOwnProperty('requiredResources')
        ? overrides.requiredResources!
        : [buildResourceRequirement(), buildResourceRequirement(), buildResourceRequirement()],
    staleCauses:
      overrides && overrides.hasOwnProperty('staleCauses')
        ? overrides.staleCauses!
        : [buildStaleCause(), buildStaleCause(), buildStaleCause()],
    staleStatus:
      overrides && overrides.hasOwnProperty('staleStatus')
        ? overrides.staleStatus!
        : Types.StaleStatus.Fresh,
    type: overrides && overrides.hasOwnProperty('type') ? overrides.type! : buildDagsterType(),
  };
};

export const buildAssetNodeDefinitionCollision = (
  overrides?: Partial<Types.AssetNodeDefinitionCollision>,
): {__typename: 'AssetNodeDefinitionCollision'} & Types.AssetNodeDefinitionCollision => {
  return {
    __typename: 'AssetNodeDefinitionCollision',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey') ? overrides.assetKey! : buildAssetKey(),
    repositories:
      overrides && overrides.hasOwnProperty('repositories')
        ? overrides.repositories!
        : [buildRepository(), buildRepository(), buildRepository()],
  };
};

export const buildAssetNotFoundError = (
  overrides?: Partial<Types.AssetNotFoundError>,
): {__typename: 'AssetNotFoundError'} & Types.AssetNotFoundError => {
  return {
    __typename: 'AssetNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'beatae',
  };
};

export const buildAssetWipeSuccess = (
  overrides?: Partial<Types.AssetWipeSuccess>,
): {__typename: 'AssetWipeSuccess'} & Types.AssetWipeSuccess => {
  return {
    __typename: 'AssetWipeSuccess',
    assetKeys:
      overrides && overrides.hasOwnProperty('assetKeys')
        ? overrides.assetKeys!
        : [buildAssetKey(), buildAssetKey(), buildAssetKey()],
  };
};

export const buildBoolMetadataEntry = (
  overrides?: Partial<Types.BoolMetadataEntry>,
): {__typename: 'BoolMetadataEntry'} & Types.BoolMetadataEntry => {
  return {
    __typename: 'BoolMetadataEntry',
    boolValue: overrides && overrides.hasOwnProperty('boolValue') ? overrides.boolValue! : true,
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'illum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'dolorum',
  };
};

export const buildCancelBackfillSuccess = (
  overrides?: Partial<Types.CancelBackfillSuccess>,
): {__typename: 'CancelBackfillSuccess'} & Types.CancelBackfillSuccess => {
  return {
    __typename: 'CancelBackfillSuccess',
    backfillId:
      overrides && overrides.hasOwnProperty('backfillId') ? overrides.backfillId! : 'animi',
  };
};

export const buildCapturedLogs = (
  overrides?: Partial<Types.CapturedLogs>,
): {__typename: 'CapturedLogs'} & Types.CapturedLogs => {
  return {
    __typename: 'CapturedLogs',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'itaque',
    logKey:
      overrides && overrides.hasOwnProperty('logKey')
        ? overrides.logKey!
        : ['voluptatum', 'animi', 'sequi'],
    stderr: overrides && overrides.hasOwnProperty('stderr') ? overrides.stderr! : 'voluptatem',
    stdout: overrides && overrides.hasOwnProperty('stdout') ? overrides.stdout! : 'nesciunt',
  };
};

export const buildCapturedLogsMetadata = (
  overrides?: Partial<Types.CapturedLogsMetadata>,
): {__typename: 'CapturedLogsMetadata'} & Types.CapturedLogsMetadata => {
  return {
    __typename: 'CapturedLogsMetadata',
    stderrDownloadUrl:
      overrides && overrides.hasOwnProperty('stderrDownloadUrl')
        ? overrides.stderrDownloadUrl!
        : 'quaerat',
    stderrLocation:
      overrides && overrides.hasOwnProperty('stderrLocation')
        ? overrides.stderrLocation!
        : 'repellat',
    stdoutDownloadUrl:
      overrides && overrides.hasOwnProperty('stdoutDownloadUrl')
        ? overrides.stdoutDownloadUrl!
        : 'soluta',
    stdoutLocation:
      overrides && overrides.hasOwnProperty('stdoutLocation')
        ? overrides.stdoutLocation!
        : 'excepturi',
  };
};

export const buildCompositeConfigType = (
  overrides?: Partial<Types.CompositeConfigType>,
): {__typename: 'CompositeConfigType'} & Types.CompositeConfigType => {
  return {
    __typename: 'CompositeConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'deleniti',
    fields:
      overrides && overrides.hasOwnProperty('fields')
        ? overrides.fields!
        : [buildConfigTypeField(), buildConfigTypeField(), buildConfigTypeField()],
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'nulla',
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [buildConfigType(), buildConfigType(), buildConfigType()],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys')
        ? overrides.typeParamKeys!
        : ['eligendi', 'neque', 'qui'],
  };
};

export const buildCompositeSolidDefinition = (
  overrides?: Partial<Types.CompositeSolidDefinition>,
): {__typename: 'CompositeSolidDefinition'} & Types.CompositeSolidDefinition => {
  return {
    __typename: 'CompositeSolidDefinition',
    assetNodes:
      overrides && overrides.hasOwnProperty('assetNodes')
        ? overrides.assetNodes!
        : [buildAssetNode(), buildAssetNode(), buildAssetNode()],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'at',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '21c69675-bf11-4093-8cc2-4e3c64e910c9',
    inputDefinitions:
      overrides && overrides.hasOwnProperty('inputDefinitions')
        ? overrides.inputDefinitions!
        : [buildInputDefinition(), buildInputDefinition(), buildInputDefinition()],
    inputMappings:
      overrides && overrides.hasOwnProperty('inputMappings')
        ? overrides.inputMappings!
        : [buildInputMapping(), buildInputMapping(), buildInputMapping()],
    metadata:
      overrides && overrides.hasOwnProperty('metadata')
        ? overrides.metadata!
        : [
            buildMetadataItemDefinition(),
            buildMetadataItemDefinition(),
            buildMetadataItemDefinition(),
          ],
    modes:
      overrides && overrides.hasOwnProperty('modes')
        ? overrides.modes!
        : [buildMode(), buildMode(), buildMode()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'consequatur',
    outputDefinitions:
      overrides && overrides.hasOwnProperty('outputDefinitions')
        ? overrides.outputDefinitions!
        : [buildOutputDefinition(), buildOutputDefinition(), buildOutputDefinition()],
    outputMappings:
      overrides && overrides.hasOwnProperty('outputMappings')
        ? overrides.outputMappings!
        : [buildOutputMapping(), buildOutputMapping(), buildOutputMapping()],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : buildSolidHandle(),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles')
        ? overrides.solidHandles!
        : [buildSolidHandle(), buildSolidHandle(), buildSolidHandle()],
    solids:
      overrides && overrides.hasOwnProperty('solids')
        ? overrides.solids!
        : [buildSolid(), buildSolid(), buildSolid()],
  };
};

export const buildComputeLogFile = (
  overrides?: Partial<Types.ComputeLogFile>,
): {__typename: 'ComputeLogFile'} & Types.ComputeLogFile => {
  return {
    __typename: 'ComputeLogFile',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 1566,
    data: overrides && overrides.hasOwnProperty('data') ? overrides.data! : 'quia',
    downloadUrl:
      overrides && overrides.hasOwnProperty('downloadUrl') ? overrides.downloadUrl! : 'sed',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : 'beatae',
    size: overrides && overrides.hasOwnProperty('size') ? overrides.size! : 7860,
  };
};

export const buildComputeLogs = (
  overrides?: Partial<Types.ComputeLogs>,
): {__typename: 'ComputeLogs'} & Types.ComputeLogs => {
  return {
    __typename: 'ComputeLogs',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'est',
    stderr:
      overrides && overrides.hasOwnProperty('stderr') ? overrides.stderr! : buildComputeLogFile(),
    stdout:
      overrides && overrides.hasOwnProperty('stdout') ? overrides.stdout! : buildComputeLogFile(),
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'cum',
  };
};

export const buildConfigType = (
  overrides?: Partial<Types.ConfigType>,
): {__typename: 'ConfigType'} & Types.ConfigType => {
  return {
    __typename: 'ConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'nostrum',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'earum',
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [buildConfigType(), buildConfigType(), buildConfigType()],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys')
        ? overrides.typeParamKeys!
        : ['qui', 'tempore', 'omnis'],
  };
};

export const buildConfigTypeField = (
  overrides?: Partial<Types.ConfigTypeField>,
): {__typename: 'ConfigTypeField'} & Types.ConfigTypeField => {
  return {
    __typename: 'ConfigTypeField',
    configType:
      overrides && overrides.hasOwnProperty('configType')
        ? overrides.configType!
        : buildConfigType(),
    configTypeKey:
      overrides && overrides.hasOwnProperty('configTypeKey')
        ? overrides.configTypeKey!
        : 'perspiciatis',
    defaultValueAsJson:
      overrides && overrides.hasOwnProperty('defaultValueAsJson')
        ? overrides.defaultValueAsJson!
        : 'dolorum',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'esse',
    isRequired: overrides && overrides.hasOwnProperty('isRequired') ? overrides.isRequired! : true,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'odit',
  };
};

export const buildConfigTypeNotFoundError = (
  overrides?: Partial<Types.ConfigTypeNotFoundError>,
): {__typename: 'ConfigTypeNotFoundError'} & Types.ConfigTypeNotFoundError => {
  return {
    __typename: 'ConfigTypeNotFoundError',
    configTypeName:
      overrides && overrides.hasOwnProperty('configTypeName') ? overrides.configTypeName! : 'ullam',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'suscipit',
    pipeline:
      overrides && overrides.hasOwnProperty('pipeline') ? overrides.pipeline! : buildPipeline(),
  };
};

export const buildConfiguredValue = (
  overrides?: Partial<Types.ConfiguredValue>,
): {__typename: 'ConfiguredValue'} & Types.ConfiguredValue => {
  return {
    __typename: 'ConfiguredValue',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'ipsam',
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : Types.ConfiguredValueType.EnvVar,
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'distinctio',
  };
};

export const buildConflictingExecutionParamsError = (
  overrides?: Partial<Types.ConflictingExecutionParamsError>,
): {__typename: 'ConflictingExecutionParamsError'} & Types.ConflictingExecutionParamsError => {
  return {
    __typename: 'ConflictingExecutionParamsError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'pariatur',
  };
};

export const buildDaemonHealth = (
  overrides?: Partial<Types.DaemonHealth>,
): {__typename: 'DaemonHealth'} & Types.DaemonHealth => {
  return {
    __typename: 'DaemonHealth',
    allDaemonStatuses:
      overrides && overrides.hasOwnProperty('allDaemonStatuses')
        ? overrides.allDaemonStatuses!
        : [buildDaemonStatus(), buildDaemonStatus(), buildDaemonStatus()],
    daemonStatus:
      overrides && overrides.hasOwnProperty('daemonStatus')
        ? overrides.daemonStatus!
        : buildDaemonStatus(),
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'omnis',
  };
};

export const buildDaemonStatus = (
  overrides?: Partial<Types.DaemonStatus>,
): {__typename: 'DaemonStatus'} & Types.DaemonStatus => {
  return {
    __typename: 'DaemonStatus',
    daemonType:
      overrides && overrides.hasOwnProperty('daemonType') ? overrides.daemonType! : 'deleniti',
    healthy: overrides && overrides.hasOwnProperty('healthy') ? overrides.healthy! : true,
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'a8655b08-07f7-4c28-8899-b5c2d0466295',
    lastHeartbeatErrors:
      overrides && overrides.hasOwnProperty('lastHeartbeatErrors')
        ? overrides.lastHeartbeatErrors!
        : [buildPythonError(), buildPythonError(), buildPythonError()],
    lastHeartbeatTime:
      overrides && overrides.hasOwnProperty('lastHeartbeatTime')
        ? overrides.lastHeartbeatTime!
        : 8.69,
    required: overrides && overrides.hasOwnProperty('required') ? overrides.required! : false,
  };
};

export const buildDagitMutation = (
  overrides?: Partial<Types.DagitMutation>,
): {__typename: 'DagitMutation'} & Types.DagitMutation => {
  return {
    __typename: 'DagitMutation',
    addDynamicPartition:
      overrides && overrides.hasOwnProperty('addDynamicPartition')
        ? overrides.addDynamicPartition!
        : buildAddDynamicPartitionSuccess(),
    cancelPartitionBackfill:
      overrides && overrides.hasOwnProperty('cancelPartitionBackfill')
        ? overrides.cancelPartitionBackfill!
        : buildCancelBackfillSuccess(),
    deletePipelineRun:
      overrides && overrides.hasOwnProperty('deletePipelineRun')
        ? overrides.deletePipelineRun!
        : buildDeletePipelineRunSuccess(),
    deleteRun:
      overrides && overrides.hasOwnProperty('deleteRun')
        ? overrides.deleteRun!
        : buildDeletePipelineRunSuccess(),
    launchPartitionBackfill:
      overrides && overrides.hasOwnProperty('launchPartitionBackfill')
        ? overrides.launchPartitionBackfill!
        : buildConflictingExecutionParamsError(),
    launchPipelineExecution:
      overrides && overrides.hasOwnProperty('launchPipelineExecution')
        ? overrides.launchPipelineExecution!
        : buildConflictingExecutionParamsError(),
    launchPipelineReexecution:
      overrides && overrides.hasOwnProperty('launchPipelineReexecution')
        ? overrides.launchPipelineReexecution!
        : buildConflictingExecutionParamsError(),
    launchRun:
      overrides && overrides.hasOwnProperty('launchRun')
        ? overrides.launchRun!
        : buildConflictingExecutionParamsError(),
    launchRunReexecution:
      overrides && overrides.hasOwnProperty('launchRunReexecution')
        ? overrides.launchRunReexecution!
        : buildConflictingExecutionParamsError(),
    logTelemetry:
      overrides && overrides.hasOwnProperty('logTelemetry')
        ? overrides.logTelemetry!
        : buildLogTelemetrySuccess(),
    reloadRepositoryLocation:
      overrides && overrides.hasOwnProperty('reloadRepositoryLocation')
        ? overrides.reloadRepositoryLocation!
        : buildPythonError(),
    reloadWorkspace:
      overrides && overrides.hasOwnProperty('reloadWorkspace')
        ? overrides.reloadWorkspace!
        : buildPythonError(),
    resumePartitionBackfill:
      overrides && overrides.hasOwnProperty('resumePartitionBackfill')
        ? overrides.resumePartitionBackfill!
        : buildPythonError(),
    scheduleDryRun:
      overrides && overrides.hasOwnProperty('scheduleDryRun')
        ? overrides.scheduleDryRun!
        : buildDryRunInstigationTick(),
    sensorDryRun:
      overrides && overrides.hasOwnProperty('sensorDryRun')
        ? overrides.sensorDryRun!
        : buildDryRunInstigationTick(),
    setNuxSeen: overrides && overrides.hasOwnProperty('setNuxSeen') ? overrides.setNuxSeen! : true,
    setSensorCursor:
      overrides && overrides.hasOwnProperty('setSensorCursor')
        ? overrides.setSensorCursor!
        : buildPythonError(),
    shutdownRepositoryLocation:
      overrides && overrides.hasOwnProperty('shutdownRepositoryLocation')
        ? overrides.shutdownRepositoryLocation!
        : buildPythonError(),
    startSchedule:
      overrides && overrides.hasOwnProperty('startSchedule')
        ? overrides.startSchedule!
        : buildPythonError(),
    startSensor:
      overrides && overrides.hasOwnProperty('startSensor')
        ? overrides.startSensor!
        : buildPythonError(),
    stopRunningSchedule:
      overrides && overrides.hasOwnProperty('stopRunningSchedule')
        ? overrides.stopRunningSchedule!
        : buildPythonError(),
    stopSensor:
      overrides && overrides.hasOwnProperty('stopSensor')
        ? overrides.stopSensor!
        : buildPythonError(),
    terminatePipelineExecution:
      overrides && overrides.hasOwnProperty('terminatePipelineExecution')
        ? overrides.terminatePipelineExecution!
        : buildPythonError(),
    terminateRun:
      overrides && overrides.hasOwnProperty('terminateRun')
        ? overrides.terminateRun!
        : buildPythonError(),
    wipeAssets:
      overrides && overrides.hasOwnProperty('wipeAssets')
        ? overrides.wipeAssets!
        : buildAssetNotFoundError(),
  };
};

export const buildDagitQuery = (
  overrides?: Partial<Types.DagitQuery>,
): {__typename: 'DagitQuery'} & Types.DagitQuery => {
  return {
    __typename: 'DagitQuery',
    allTopLevelResourceDetailsOrError:
      overrides && overrides.hasOwnProperty('allTopLevelResourceDetailsOrError')
        ? overrides.allTopLevelResourceDetailsOrError!
        : buildPythonError(),
    assetNodeDefinitionCollisions:
      overrides && overrides.hasOwnProperty('assetNodeDefinitionCollisions')
        ? overrides.assetNodeDefinitionCollisions!
        : [
            buildAssetNodeDefinitionCollision(),
            buildAssetNodeDefinitionCollision(),
            buildAssetNodeDefinitionCollision(),
          ],
    assetNodeOrError:
      overrides && overrides.hasOwnProperty('assetNodeOrError')
        ? overrides.assetNodeOrError!
        : buildAssetNode(),
    assetNodes:
      overrides && overrides.hasOwnProperty('assetNodes')
        ? overrides.assetNodes!
        : [buildAssetNode(), buildAssetNode(), buildAssetNode()],
    assetOrError:
      overrides && overrides.hasOwnProperty('assetOrError')
        ? overrides.assetOrError!
        : buildAsset(),
    assetsLatestInfo:
      overrides && overrides.hasOwnProperty('assetsLatestInfo')
        ? overrides.assetsLatestInfo!
        : [buildAssetLatestInfo(), buildAssetLatestInfo(), buildAssetLatestInfo()],
    assetsOrError:
      overrides && overrides.hasOwnProperty('assetsOrError')
        ? overrides.assetsOrError!
        : buildAssetConnection(),
    capturedLogs:
      overrides && overrides.hasOwnProperty('capturedLogs')
        ? overrides.capturedLogs!
        : buildCapturedLogs(),
    capturedLogsMetadata:
      overrides && overrides.hasOwnProperty('capturedLogsMetadata')
        ? overrides.capturedLogsMetadata!
        : buildCapturedLogsMetadata(),
    executionPlanOrError:
      overrides && overrides.hasOwnProperty('executionPlanOrError')
        ? overrides.executionPlanOrError!
        : buildExecutionPlan(),
    graphOrError:
      overrides && overrides.hasOwnProperty('graphOrError')
        ? overrides.graphOrError!
        : buildGraph(),
    instance:
      overrides && overrides.hasOwnProperty('instance') ? overrides.instance! : buildInstance(),
    instigationStateOrError:
      overrides && overrides.hasOwnProperty('instigationStateOrError')
        ? overrides.instigationStateOrError!
        : buildInstigationState(),
    isPipelineConfigValid:
      overrides && overrides.hasOwnProperty('isPipelineConfigValid')
        ? overrides.isPipelineConfigValid!
        : buildInvalidSubsetError(),
    locationStatusesOrError:
      overrides && overrides.hasOwnProperty('locationStatusesOrError')
        ? overrides.locationStatusesOrError!
        : buildPythonError(),
    logsForRun:
      overrides && overrides.hasOwnProperty('logsForRun')
        ? overrides.logsForRun!
        : buildEventConnection(),
    partitionBackfillOrError:
      overrides && overrides.hasOwnProperty('partitionBackfillOrError')
        ? overrides.partitionBackfillOrError!
        : buildPartitionBackfill(),
    partitionBackfillsOrError:
      overrides && overrides.hasOwnProperty('partitionBackfillsOrError')
        ? overrides.partitionBackfillsOrError!
        : buildPartitionBackfills(),
    partitionSetOrError:
      overrides && overrides.hasOwnProperty('partitionSetOrError')
        ? overrides.partitionSetOrError!
        : buildPartitionSet(),
    partitionSetsOrError:
      overrides && overrides.hasOwnProperty('partitionSetsOrError')
        ? overrides.partitionSetsOrError!
        : buildPartitionSets(),
    permissions:
      overrides && overrides.hasOwnProperty('permissions')
        ? overrides.permissions!
        : [buildPermission(), buildPermission(), buildPermission()],
    pipelineOrError:
      overrides && overrides.hasOwnProperty('pipelineOrError')
        ? overrides.pipelineOrError!
        : buildInvalidSubsetError(),
    pipelineRunOrError:
      overrides && overrides.hasOwnProperty('pipelineRunOrError')
        ? overrides.pipelineRunOrError!
        : buildPythonError(),
    pipelineRunsOrError:
      overrides && overrides.hasOwnProperty('pipelineRunsOrError')
        ? overrides.pipelineRunsOrError!
        : buildInvalidPipelineRunsFilterError(),
    pipelineSnapshotOrError:
      overrides && overrides.hasOwnProperty('pipelineSnapshotOrError')
        ? overrides.pipelineSnapshotOrError!
        : buildPipelineNotFoundError(),
    repositoriesOrError:
      overrides && overrides.hasOwnProperty('repositoriesOrError')
        ? overrides.repositoriesOrError!
        : buildPythonError(),
    repositoryOrError:
      overrides && overrides.hasOwnProperty('repositoryOrError')
        ? overrides.repositoryOrError!
        : buildPythonError(),
    runConfigSchemaOrError:
      overrides && overrides.hasOwnProperty('runConfigSchemaOrError')
        ? overrides.runConfigSchemaOrError!
        : buildInvalidSubsetError(),
    runGroupOrError:
      overrides && overrides.hasOwnProperty('runGroupOrError')
        ? overrides.runGroupOrError!
        : buildPythonError(),
    runGroupsOrError:
      overrides && overrides.hasOwnProperty('runGroupsOrError')
        ? overrides.runGroupsOrError!
        : buildRunGroupsOrError(),
    runOrError:
      overrides && overrides.hasOwnProperty('runOrError')
        ? overrides.runOrError!
        : buildPythonError(),
    runTagKeysOrError:
      overrides && overrides.hasOwnProperty('runTagKeysOrError')
        ? overrides.runTagKeysOrError!
        : buildPythonError(),
    runTagsOrError:
      overrides && overrides.hasOwnProperty('runTagsOrError')
        ? overrides.runTagsOrError!
        : buildPythonError(),
    runsOrError:
      overrides && overrides.hasOwnProperty('runsOrError')
        ? overrides.runsOrError!
        : buildInvalidPipelineRunsFilterError(),
    scheduleOrError:
      overrides && overrides.hasOwnProperty('scheduleOrError')
        ? overrides.scheduleOrError!
        : buildPythonError(),
    scheduler:
      overrides && overrides.hasOwnProperty('scheduler')
        ? overrides.scheduler!
        : buildPythonError(),
    schedulesOrError:
      overrides && overrides.hasOwnProperty('schedulesOrError')
        ? overrides.schedulesOrError!
        : buildPythonError(),
    sensorOrError:
      overrides && overrides.hasOwnProperty('sensorOrError')
        ? overrides.sensorOrError!
        : buildPythonError(),
    sensorsOrError:
      overrides && overrides.hasOwnProperty('sensorsOrError')
        ? overrides.sensorsOrError!
        : buildPythonError(),
    shouldShowNux:
      overrides && overrides.hasOwnProperty('shouldShowNux') ? overrides.shouldShowNux! : true,
    test: overrides && overrides.hasOwnProperty('test') ? overrides.test! : buildTestFields(),
    topLevelResourceDetailsOrError:
      overrides && overrides.hasOwnProperty('topLevelResourceDetailsOrError')
        ? overrides.topLevelResourceDetailsOrError!
        : buildPythonError(),
    unloadableInstigationStatesOrError:
      overrides && overrides.hasOwnProperty('unloadableInstigationStatesOrError')
        ? overrides.unloadableInstigationStatesOrError!
        : buildInstigationStates(),
    utilizedEnvVarsOrError:
      overrides && overrides.hasOwnProperty('utilizedEnvVarsOrError')
        ? overrides.utilizedEnvVarsOrError!
        : buildEnvVarWithConsumersList(),
    version: overrides && overrides.hasOwnProperty('version') ? overrides.version! : 'sed',
    workspaceOrError:
      overrides && overrides.hasOwnProperty('workspaceOrError')
        ? overrides.workspaceOrError!
        : buildPythonError(),
  };
};

export const buildDagitSubscription = (
  overrides?: Partial<Types.DagitSubscription>,
): {__typename: 'DagitSubscription'} & Types.DagitSubscription => {
  return {
    __typename: 'DagitSubscription',
    capturedLogs:
      overrides && overrides.hasOwnProperty('capturedLogs')
        ? overrides.capturedLogs!
        : buildCapturedLogs(),
    computeLogs:
      overrides && overrides.hasOwnProperty('computeLogs')
        ? overrides.computeLogs!
        : buildComputeLogFile(),
    locationStateChangeEvents:
      overrides && overrides.hasOwnProperty('locationStateChangeEvents')
        ? overrides.locationStateChangeEvents!
        : buildLocationStateChangeSubscription(),
    pipelineRunLogs:
      overrides && overrides.hasOwnProperty('pipelineRunLogs')
        ? overrides.pipelineRunLogs!
        : buildPipelineRunLogsSubscriptionFailure(),
  };
};

export const buildDagsterLibraryVersion = (
  overrides?: Partial<Types.DagsterLibraryVersion>,
): {__typename: 'DagsterLibraryVersion'} & Types.DagsterLibraryVersion => {
  return {
    __typename: 'DagsterLibraryVersion',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'et',
    version: overrides && overrides.hasOwnProperty('version') ? overrides.version! : 'qui',
  };
};

export const buildDagsterType = (
  overrides?: Partial<Types.DagsterType>,
): {__typename: 'DagsterType'} & Types.DagsterType => {
  return {
    __typename: 'DagsterType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'sed',
    displayName:
      overrides && overrides.hasOwnProperty('displayName') ? overrides.displayName! : 'consequatur',
    innerTypes:
      overrides && overrides.hasOwnProperty('innerTypes')
        ? overrides.innerTypes!
        : [buildDagsterType(), buildDagsterType(), buildDagsterType()],
    inputSchemaType:
      overrides && overrides.hasOwnProperty('inputSchemaType')
        ? overrides.inputSchemaType!
        : buildConfigType(),
    isBuiltin: overrides && overrides.hasOwnProperty('isBuiltin') ? overrides.isBuiltin! : true,
    isList: overrides && overrides.hasOwnProperty('isList') ? overrides.isList! : true,
    isNothing: overrides && overrides.hasOwnProperty('isNothing') ? overrides.isNothing! : true,
    isNullable: overrides && overrides.hasOwnProperty('isNullable') ? overrides.isNullable! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'sed',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'eum',
    outputSchemaType:
      overrides && overrides.hasOwnProperty('outputSchemaType')
        ? overrides.outputSchemaType!
        : buildConfigType(),
  };
};

export const buildDagsterTypeNotFoundError = (
  overrides?: Partial<Types.DagsterTypeNotFoundError>,
): {__typename: 'DagsterTypeNotFoundError'} & Types.DagsterTypeNotFoundError => {
  return {
    __typename: 'DagsterTypeNotFoundError',
    dagsterTypeName:
      overrides && overrides.hasOwnProperty('dagsterTypeName')
        ? overrides.dagsterTypeName!
        : 'quia',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'dolore',
  };
};

export const buildDefaultPartitions = (
  overrides?: Partial<Types.DefaultPartitions>,
): {__typename: 'DefaultPartitions'} & Types.DefaultPartitions => {
  return {
    __typename: 'DefaultPartitions',
    failedPartitions:
      overrides && overrides.hasOwnProperty('failedPartitions')
        ? overrides.failedPartitions!
        : ['hic', 'et', 'veniam'],
    materializedPartitions:
      overrides && overrides.hasOwnProperty('materializedPartitions')
        ? overrides.materializedPartitions!
        : ['quis', 'ea', 'earum'],
    unmaterializedPartitions:
      overrides && overrides.hasOwnProperty('unmaterializedPartitions')
        ? overrides.unmaterializedPartitions!
        : ['esse', 'aut', 'nihil'],
  };
};

export const buildDeletePipelineRunSuccess = (
  overrides?: Partial<Types.DeletePipelineRunSuccess>,
): {__typename: 'DeletePipelineRunSuccess'} & Types.DeletePipelineRunSuccess => {
  return {
    __typename: 'DeletePipelineRunSuccess',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'ipsum',
  };
};

export const buildDeleteRunMutation = (
  overrides?: Partial<Types.DeleteRunMutation>,
): {__typename: 'DeleteRunMutation'} & Types.DeleteRunMutation => {
  return {
    __typename: 'DeleteRunMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : buildDeletePipelineRunSuccess(),
  };
};

export const buildDimensionDefinitionType = (
  overrides?: Partial<Types.DimensionDefinitionType>,
): {__typename: 'DimensionDefinitionType'} & Types.DimensionDefinitionType => {
  return {
    __typename: 'DimensionDefinitionType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'aut',
    isPrimaryDimension:
      overrides && overrides.hasOwnProperty('isPrimaryDimension')
        ? overrides.isPrimaryDimension!
        : true,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'vel',
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : Types.PartitionDefinitionType.Dynamic,
  };
};

export const buildDimensionPartitionKeys = (
  overrides?: Partial<Types.DimensionPartitionKeys>,
): {__typename: 'DimensionPartitionKeys'} & Types.DimensionPartitionKeys => {
  return {
    __typename: 'DimensionPartitionKeys',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'id',
    partitionKeys:
      overrides && overrides.hasOwnProperty('partitionKeys')
        ? overrides.partitionKeys!
        : ['exercitationem', 'explicabo', 'dolore'],
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : Types.PartitionDefinitionType.Dynamic,
  };
};

export const buildDisplayableEvent = (
  overrides?: Partial<Types.DisplayableEvent>,
): {__typename: 'DisplayableEvent'} & Types.DisplayableEvent => {
  return {
    __typename: 'DisplayableEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'pariatur',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'ipsa',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
  };
};

export const buildDryRunInstigationTick = (
  overrides?: Partial<Types.DryRunInstigationTick>,
): {__typename: 'DryRunInstigationTick'} & Types.DryRunInstigationTick => {
  return {
    __typename: 'DryRunInstigationTick',
    evaluationResult:
      overrides && overrides.hasOwnProperty('evaluationResult')
        ? overrides.evaluationResult!
        : buildTickEvaluation(),
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 7.53,
  };
};

export const buildDryRunInstigationTicks = (
  overrides?: Partial<Types.DryRunInstigationTicks>,
): {__typename: 'DryRunInstigationTicks'} & Types.DryRunInstigationTicks => {
  return {
    __typename: 'DryRunInstigationTicks',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 0.85,
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [
            buildDryRunInstigationTick(),
            buildDryRunInstigationTick(),
            buildDryRunInstigationTick(),
          ],
  };
};

export const buildDuplicateDynamicPartitionError = (
  overrides?: Partial<Types.DuplicateDynamicPartitionError>,
): {__typename: 'DuplicateDynamicPartitionError'} & Types.DuplicateDynamicPartitionError => {
  return {
    __typename: 'DuplicateDynamicPartitionError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quae',
    partitionName:
      overrides && overrides.hasOwnProperty('partitionName') ? overrides.partitionName! : 'quod',
    partitionsDefName:
      overrides && overrides.hasOwnProperty('partitionsDefName')
        ? overrides.partitionsDefName!
        : 'natus',
  };
};

export const buildEngineEvent = (
  overrides?: Partial<Types.EngineEvent>,
): {__typename: 'EngineEvent'} & Types.EngineEvent => {
  return {
    __typename: 'EngineEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'a',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'aut',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'saepe',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'unde',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'doloribus',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'aut',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'quo',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'beatae',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'minima',
  };
};

export const buildEnumConfigType = (
  overrides?: Partial<Types.EnumConfigType>,
): {__typename: 'EnumConfigType'} & Types.EnumConfigType => {
  return {
    __typename: 'EnumConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'nostrum',
    givenName:
      overrides && overrides.hasOwnProperty('givenName') ? overrides.givenName! : 'reprehenderit',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'repudiandae',
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [buildConfigType(), buildConfigType(), buildConfigType()],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys')
        ? overrides.typeParamKeys!
        : ['ut', 'quis', 'harum'],
    values:
      overrides && overrides.hasOwnProperty('values')
        ? overrides.values!
        : [buildEnumConfigValue(), buildEnumConfigValue(), buildEnumConfigValue()],
  };
};

export const buildEnumConfigValue = (
  overrides?: Partial<Types.EnumConfigValue>,
): {__typename: 'EnumConfigValue'} & Types.EnumConfigValue => {
  return {
    __typename: 'EnumConfigValue',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'dignissimos',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'necessitatibus',
  };
};

export const buildEnvVarConsumer = (
  overrides?: Partial<Types.EnvVarConsumer>,
): {__typename: 'EnvVarConsumer'} & Types.EnvVarConsumer => {
  return {
    __typename: 'EnvVarConsumer',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'est',
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : Types.EnvVarConsumerType.Resource,
  };
};

export const buildEnvVarWithConsumers = (
  overrides?: Partial<Types.EnvVarWithConsumers>,
): {__typename: 'EnvVarWithConsumers'} & Types.EnvVarWithConsumers => {
  return {
    __typename: 'EnvVarWithConsumers',
    envVarConsumers:
      overrides && overrides.hasOwnProperty('envVarConsumers')
        ? overrides.envVarConsumers!
        : [buildEnvVarConsumer(), buildEnvVarConsumer(), buildEnvVarConsumer()],
    envVarName:
      overrides && overrides.hasOwnProperty('envVarName') ? overrides.envVarName! : 'quis',
  };
};

export const buildEnvVarWithConsumersList = (
  overrides?: Partial<Types.EnvVarWithConsumersList>,
): {__typename: 'EnvVarWithConsumersList'} & Types.EnvVarWithConsumersList => {
  return {
    __typename: 'EnvVarWithConsumersList',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildEnvVarWithConsumers(), buildEnvVarWithConsumers(), buildEnvVarWithConsumers()],
  };
};

export const buildError = (
  overrides?: Partial<Types.Error>,
): {__typename: 'Error'} & Types.Error => {
  return {
    __typename: 'Error',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
  };
};

export const buildErrorChainLink = (
  overrides?: Partial<Types.ErrorChainLink>,
): {__typename: 'ErrorChainLink'} & Types.ErrorChainLink => {
  return {
    __typename: 'ErrorChainLink',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    isExplicitLink:
      overrides && overrides.hasOwnProperty('isExplicitLink') ? overrides.isExplicitLink! : true,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ut',
  };
};

export const buildErrorEvent = (
  overrides?: Partial<Types.ErrorEvent>,
): {__typename: 'ErrorEvent'} & Types.ErrorEvent => {
  return {
    __typename: 'ErrorEvent',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
  };
};

export const buildEvaluationStack = (
  overrides?: Partial<Types.EvaluationStack>,
): {__typename: 'EvaluationStack'} & Types.EvaluationStack => {
  return {
    __typename: 'EvaluationStack',
    entries:
      overrides && overrides.hasOwnProperty('entries')
        ? overrides.entries!
        : [
            buildEvaluationStackListItemEntry(),
            buildEvaluationStackListItemEntry(),
            buildEvaluationStackListItemEntry(),
          ],
  };
};

export const buildEvaluationStackListItemEntry = (
  overrides?: Partial<Types.EvaluationStackListItemEntry>,
): {__typename: 'EvaluationStackListItemEntry'} & Types.EvaluationStackListItemEntry => {
  return {
    __typename: 'EvaluationStackListItemEntry',
    listIndex: overrides && overrides.hasOwnProperty('listIndex') ? overrides.listIndex! : 8595,
  };
};

export const buildEvaluationStackMapKeyEntry = (
  overrides?: Partial<Types.EvaluationStackMapKeyEntry>,
): {__typename: 'EvaluationStackMapKeyEntry'} & Types.EvaluationStackMapKeyEntry => {
  return {
    __typename: 'EvaluationStackMapKeyEntry',
    mapKey: overrides && overrides.hasOwnProperty('mapKey') ? overrides.mapKey! : 'qui',
  };
};

export const buildEvaluationStackMapValueEntry = (
  overrides?: Partial<Types.EvaluationStackMapValueEntry>,
): {__typename: 'EvaluationStackMapValueEntry'} & Types.EvaluationStackMapValueEntry => {
  return {
    __typename: 'EvaluationStackMapValueEntry',
    mapKey: overrides && overrides.hasOwnProperty('mapKey') ? overrides.mapKey! : 'architecto',
  };
};

export const buildEvaluationStackPathEntry = (
  overrides?: Partial<Types.EvaluationStackPathEntry>,
): {__typename: 'EvaluationStackPathEntry'} & Types.EvaluationStackPathEntry => {
  return {
    __typename: 'EvaluationStackPathEntry',
    fieldName: overrides && overrides.hasOwnProperty('fieldName') ? overrides.fieldName! : 'ipsa',
  };
};

export const buildEventConnection = (
  overrides?: Partial<Types.EventConnection>,
): {__typename: 'EventConnection'} & Types.EventConnection => {
  return {
    __typename: 'EventConnection',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'dolor',
    events:
      overrides && overrides.hasOwnProperty('events')
        ? overrides.events!
        : [buildAlertFailureEvent(), buildAlertFailureEvent(), buildAlertFailureEvent()],
    hasMore: overrides && overrides.hasOwnProperty('hasMore') ? overrides.hasMore! : true,
  };
};

export const buildEventTag = (
  overrides?: Partial<Types.EventTag>,
): {__typename: 'EventTag'} & Types.EventTag => {
  return {
    __typename: 'EventTag',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'saepe',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'laboriosam',
  };
};

export const buildExecutionMetadata = (
  overrides?: Partial<Types.ExecutionMetadata>,
): Types.ExecutionMetadata => {
  return {
    parentRunId:
      overrides && overrides.hasOwnProperty('parentRunId') ? overrides.parentRunId! : 'autem',
    rootRunId: overrides && overrides.hasOwnProperty('rootRunId') ? overrides.rootRunId! : 'ut',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'dolor',
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildExecutionTag(), buildExecutionTag(), buildExecutionTag()],
  };
};

export const buildExecutionParams = (
  overrides?: Partial<Types.ExecutionParams>,
): Types.ExecutionParams => {
  return {
    executionMetadata:
      overrides && overrides.hasOwnProperty('executionMetadata')
        ? overrides.executionMetadata!
        : buildExecutionMetadata(),
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'porro',
    preset: overrides && overrides.hasOwnProperty('preset') ? overrides.preset! : 'voluptates',
    runConfigData:
      overrides && overrides.hasOwnProperty('runConfigData')
        ? overrides.runConfigData!
        : 'nesciunt',
    selector:
      overrides && overrides.hasOwnProperty('selector')
        ? overrides.selector!
        : buildJobOrPipelineSelector(),
    stepKeys:
      overrides && overrides.hasOwnProperty('stepKeys')
        ? overrides.stepKeys!
        : ['sunt', 'culpa', 'eius'],
  };
};

export const buildExecutionPlan = (
  overrides?: Partial<Types.ExecutionPlan>,
): {__typename: 'ExecutionPlan'} & Types.ExecutionPlan => {
  return {
    __typename: 'ExecutionPlan',
    artifactsPersisted:
      overrides && overrides.hasOwnProperty('artifactsPersisted')
        ? overrides.artifactsPersisted!
        : true,
    steps:
      overrides && overrides.hasOwnProperty('steps')
        ? overrides.steps!
        : [buildExecutionStep(), buildExecutionStep(), buildExecutionStep()],
  };
};

export const buildExecutionStep = (
  overrides?: Partial<Types.ExecutionStep>,
): {__typename: 'ExecutionStep'} & Types.ExecutionStep => {
  return {
    __typename: 'ExecutionStep',
    inputs:
      overrides && overrides.hasOwnProperty('inputs')
        ? overrides.inputs!
        : [buildExecutionStepInput(), buildExecutionStepInput(), buildExecutionStepInput()],
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'ut',
    kind: overrides && overrides.hasOwnProperty('kind') ? overrides.kind! : Types.StepKind.Compute,
    metadata:
      overrides && overrides.hasOwnProperty('metadata')
        ? overrides.metadata!
        : [
            buildMetadataItemDefinition(),
            buildMetadataItemDefinition(),
            buildMetadataItemDefinition(),
          ],
    outputs:
      overrides && overrides.hasOwnProperty('outputs')
        ? overrides.outputs!
        : [buildExecutionStepOutput(), buildExecutionStepOutput(), buildExecutionStepOutput()],
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'aspernatur',
  };
};

export const buildExecutionStepFailureEvent = (
  overrides?: Partial<Types.ExecutionStepFailureEvent>,
): {__typename: 'ExecutionStepFailureEvent'} & Types.ExecutionStepFailureEvent => {
  return {
    __typename: 'ExecutionStepFailureEvent',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    errorSource:
      overrides && overrides.hasOwnProperty('errorSource')
        ? overrides.errorSource!
        : Types.ErrorSource.FrameworkError,
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    failureMetadata:
      overrides && overrides.hasOwnProperty('failureMetadata')
        ? overrides.failureMetadata!
        : buildFailureMetadata(),
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'eligendi',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'itaque',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'expedita',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'quos',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'asperiores',
  };
};

export const buildExecutionStepInput = (
  overrides?: Partial<Types.ExecutionStepInput>,
): {__typename: 'ExecutionStepInput'} & Types.ExecutionStepInput => {
  return {
    __typename: 'ExecutionStepInput',
    dependsOn:
      overrides && overrides.hasOwnProperty('dependsOn')
        ? overrides.dependsOn!
        : [buildExecutionStep(), buildExecutionStep(), buildExecutionStep()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'tempore',
  };
};

export const buildExecutionStepInputEvent = (
  overrides?: Partial<Types.ExecutionStepInputEvent>,
): {__typename: 'ExecutionStepInputEvent'} & Types.ExecutionStepInputEvent => {
  return {
    __typename: 'ExecutionStepInputEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    inputName:
      overrides && overrides.hasOwnProperty('inputName') ? overrides.inputName! : 'inventore',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'dolore',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'sit',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'animi',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'dolores',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'dolor',
    typeCheck:
      overrides && overrides.hasOwnProperty('typeCheck') ? overrides.typeCheck! : buildTypeCheck(),
  };
};

export const buildExecutionStepOutput = (
  overrides?: Partial<Types.ExecutionStepOutput>,
): {__typename: 'ExecutionStepOutput'} & Types.ExecutionStepOutput => {
  return {
    __typename: 'ExecutionStepOutput',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'rerum',
  };
};

export const buildExecutionStepOutputEvent = (
  overrides?: Partial<Types.ExecutionStepOutputEvent>,
): {__typename: 'ExecutionStepOutputEvent'} & Types.ExecutionStepOutputEvent => {
  return {
    __typename: 'ExecutionStepOutputEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'vel',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'quae',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quo',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    outputName:
      overrides && overrides.hasOwnProperty('outputName') ? overrides.outputName! : 'animi',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'repellat',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'sed',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'sed',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'ducimus',
    typeCheck:
      overrides && overrides.hasOwnProperty('typeCheck') ? overrides.typeCheck! : buildTypeCheck(),
  };
};

export const buildExecutionStepRestartEvent = (
  overrides?: Partial<Types.ExecutionStepRestartEvent>,
): {__typename: 'ExecutionStepRestartEvent'} & Types.ExecutionStepRestartEvent => {
  return {
    __typename: 'ExecutionStepRestartEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'corporis',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'corrupti',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'quo',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'iure',
  };
};

export const buildExecutionStepSkippedEvent = (
  overrides?: Partial<Types.ExecutionStepSkippedEvent>,
): {__typename: 'ExecutionStepSkippedEvent'} & Types.ExecutionStepSkippedEvent => {
  return {
    __typename: 'ExecutionStepSkippedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'est',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'aliquid',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'quos',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'vero',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'voluptates',
  };
};

export const buildExecutionStepStartEvent = (
  overrides?: Partial<Types.ExecutionStepStartEvent>,
): {__typename: 'ExecutionStepStartEvent'} & Types.ExecutionStepStartEvent => {
  return {
    __typename: 'ExecutionStepStartEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'aliquid',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'nostrum',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'voluptatem',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'omnis',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'debitis',
  };
};

export const buildExecutionStepSuccessEvent = (
  overrides?: Partial<Types.ExecutionStepSuccessEvent>,
): {__typename: 'ExecutionStepSuccessEvent'} & Types.ExecutionStepSuccessEvent => {
  return {
    __typename: 'ExecutionStepSuccessEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quam',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'non',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'aliquam',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'fuga',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'suscipit',
  };
};

export const buildExecutionStepUpForRetryEvent = (
  overrides?: Partial<Types.ExecutionStepUpForRetryEvent>,
): {__typename: 'ExecutionStepUpForRetryEvent'} & Types.ExecutionStepUpForRetryEvent => {
  return {
    __typename: 'ExecutionStepUpForRetryEvent',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'voluptas',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'maiores',
    secondsToWait:
      overrides && overrides.hasOwnProperty('secondsToWait') ? overrides.secondsToWait! : 9376,
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'nostrum',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'sed',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'ut',
  };
};

export const buildExecutionTag = (overrides?: Partial<Types.ExecutionTag>): Types.ExecutionTag => {
  return {
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'quis',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'aut',
  };
};

export const buildExpectationResult = (
  overrides?: Partial<Types.ExpectationResult>,
): {__typename: 'ExpectationResult'} & Types.ExpectationResult => {
  return {
    __typename: 'ExpectationResult',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'dignissimos',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'molestiae',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    success: overrides && overrides.hasOwnProperty('success') ? overrides.success! : false,
  };
};

export const buildFailureMetadata = (
  overrides?: Partial<Types.FailureMetadata>,
): {__typename: 'FailureMetadata'} & Types.FailureMetadata => {
  return {
    __typename: 'FailureMetadata',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'ex',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'unde',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
  };
};

export const buildFieldNotDefinedConfigError = (
  overrides?: Partial<Types.FieldNotDefinedConfigError>,
): {__typename: 'FieldNotDefinedConfigError'} & Types.FieldNotDefinedConfigError => {
  return {
    __typename: 'FieldNotDefinedConfigError',
    fieldName:
      overrides && overrides.hasOwnProperty('fieldName') ? overrides.fieldName! : 'voluptatem',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ut',
    path:
      overrides && overrides.hasOwnProperty('path') ? overrides.path! : ['quidem', 'sunt', 'quam'],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : Types.EvaluationErrorReason.FieldsNotDefined,
    stack:
      overrides && overrides.hasOwnProperty('stack') ? overrides.stack! : buildEvaluationStack(),
  };
};

export const buildFieldsNotDefinedConfigError = (
  overrides?: Partial<Types.FieldsNotDefinedConfigError>,
): {__typename: 'FieldsNotDefinedConfigError'} & Types.FieldsNotDefinedConfigError => {
  return {
    __typename: 'FieldsNotDefinedConfigError',
    fieldNames:
      overrides && overrides.hasOwnProperty('fieldNames')
        ? overrides.fieldNames!
        : ['autem', 'ab', 'architecto'],
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'dolore',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : ['ullam', 'ea', 'ut'],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : Types.EvaluationErrorReason.FieldsNotDefined,
    stack:
      overrides && overrides.hasOwnProperty('stack') ? overrides.stack! : buildEvaluationStack(),
  };
};

export const buildFloatMetadataEntry = (
  overrides?: Partial<Types.FloatMetadataEntry>,
): {__typename: 'FloatMetadataEntry'} & Types.FloatMetadataEntry => {
  return {
    __typename: 'FloatMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'iusto',
    floatValue: overrides && overrides.hasOwnProperty('floatValue') ? overrides.floatValue! : 5.68,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'velit',
  };
};

export const buildFreshnessPolicy = (
  overrides?: Partial<Types.FreshnessPolicy>,
): {__typename: 'FreshnessPolicy'} & Types.FreshnessPolicy => {
  return {
    __typename: 'FreshnessPolicy',
    cronSchedule:
      overrides && overrides.hasOwnProperty('cronSchedule') ? overrides.cronSchedule! : 'illo',
    cronScheduleTimezone:
      overrides && overrides.hasOwnProperty('cronScheduleTimezone')
        ? overrides.cronScheduleTimezone!
        : 'recusandae',
    maximumLagMinutes:
      overrides && overrides.hasOwnProperty('maximumLagMinutes')
        ? overrides.maximumLagMinutes!
        : 6.15,
  };
};

export const buildGraph = (
  overrides?: Partial<Types.Graph>,
): {__typename: 'Graph'} & Types.Graph => {
  return {
    __typename: 'Graph',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'aspernatur',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '000b66d3-d51f-4db4-9757-da36cd59fc26',
    modes:
      overrides && overrides.hasOwnProperty('modes')
        ? overrides.modes!
        : [buildMode(), buildMode(), buildMode()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'quidem',
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : buildSolidHandle(),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles')
        ? overrides.solidHandles!
        : [buildSolidHandle(), buildSolidHandle(), buildSolidHandle()],
    solids:
      overrides && overrides.hasOwnProperty('solids')
        ? overrides.solids!
        : [buildSolid(), buildSolid(), buildSolid()],
  };
};

export const buildGraphNotFoundError = (
  overrides?: Partial<Types.GraphNotFoundError>,
): {__typename: 'GraphNotFoundError'} & Types.GraphNotFoundError => {
  return {
    __typename: 'GraphNotFoundError',
    graphName: overrides && overrides.hasOwnProperty('graphName') ? overrides.graphName! : 'odio',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'autem',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'excepturi',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'ipsa',
  };
};

export const buildGraphSelector = (
  overrides?: Partial<Types.GraphSelector>,
): Types.GraphSelector => {
  return {
    graphName: overrides && overrides.hasOwnProperty('graphName') ? overrides.graphName! : 'sunt',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'nemo',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName')
        ? overrides.repositoryName!
        : 'perferendis',
  };
};

export const buildHandledOutputEvent = (
  overrides?: Partial<Types.HandledOutputEvent>,
): {__typename: 'HandledOutputEvent'} & Types.HandledOutputEvent => {
  return {
    __typename: 'HandledOutputEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quibusdam',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'ducimus',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    managerKey:
      overrides && overrides.hasOwnProperty('managerKey') ? overrides.managerKey! : 'ipsa',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'id',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    outputName:
      overrides && overrides.hasOwnProperty('outputName') ? overrides.outputName! : 'consequatur',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'perferendis',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'dolor',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'dolorum',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'nisi',
  };
};

export const buildHookCompletedEvent = (
  overrides?: Partial<Types.HookCompletedEvent>,
): {__typename: 'HookCompletedEvent'} & Types.HookCompletedEvent => {
  return {
    __typename: 'HookCompletedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'aspernatur',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'iusto',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'labore',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'atque',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'qui',
  };
};

export const buildHookErroredEvent = (
  overrides?: Partial<Types.HookErroredEvent>,
): {__typename: 'HookErroredEvent'} & Types.HookErroredEvent => {
  return {
    __typename: 'HookErroredEvent',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'molestias',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'voluptate',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'labore',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'possimus',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'qui',
  };
};

export const buildHookSkippedEvent = (
  overrides?: Partial<Types.HookSkippedEvent>,
): {__typename: 'HookSkippedEvent'} & Types.HookSkippedEvent => {
  return {
    __typename: 'HookSkippedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'id',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'iste',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'quia',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'aperiam',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'eaque',
  };
};

export const buildIPipelineSnapshot = (
  overrides?: Partial<Types.IPipelineSnapshot>,
): {__typename: 'IPipelineSnapshot'} & Types.IPipelineSnapshot => {
  return {
    __typename: 'IPipelineSnapshot',
    dagsterTypeOrError:
      overrides && overrides.hasOwnProperty('dagsterTypeOrError')
        ? overrides.dagsterTypeOrError!
        : buildDagsterTypeNotFoundError(),
    dagsterTypes:
      overrides && overrides.hasOwnProperty('dagsterTypes')
        ? overrides.dagsterTypes!
        : [buildDagsterType(), buildDagsterType(), buildDagsterType()],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'velit',
    graphName:
      overrides && overrides.hasOwnProperty('graphName') ? overrides.graphName! : 'aperiam',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    modes:
      overrides && overrides.hasOwnProperty('modes')
        ? overrides.modes!
        : [buildMode(), buildMode(), buildMode()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'autem',
    parentSnapshotId:
      overrides && overrides.hasOwnProperty('parentSnapshotId')
        ? overrides.parentSnapshotId!
        : 'deserunt',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'quo',
    runs:
      overrides && overrides.hasOwnProperty('runs')
        ? overrides.runs!
        : [buildRun(), buildRun(), buildRun()],
    schedules:
      overrides && overrides.hasOwnProperty('schedules')
        ? overrides.schedules!
        : [buildSchedule(), buildSchedule(), buildSchedule()],
    sensors:
      overrides && overrides.hasOwnProperty('sensors')
        ? overrides.sensors!
        : [buildSensor(), buildSensor(), buildSensor()],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : buildSolidHandle(),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles')
        ? overrides.solidHandles!
        : [buildSolidHandle(), buildSolidHandle(), buildSolidHandle()],
    solids:
      overrides && overrides.hasOwnProperty('solids')
        ? overrides.solids!
        : [buildSolid(), buildSolid(), buildSolid()],
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildPipelineTag(), buildPipelineTag(), buildPipelineTag()],
  };
};

export const buildISolidDefinition = (
  overrides?: Partial<Types.ISolidDefinition>,
): {__typename: 'ISolidDefinition'} & Types.ISolidDefinition => {
  return {
    __typename: 'ISolidDefinition',
    assetNodes:
      overrides && overrides.hasOwnProperty('assetNodes')
        ? overrides.assetNodes!
        : [buildAssetNode(), buildAssetNode(), buildAssetNode()],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'et',
    inputDefinitions:
      overrides && overrides.hasOwnProperty('inputDefinitions')
        ? overrides.inputDefinitions!
        : [buildInputDefinition(), buildInputDefinition(), buildInputDefinition()],
    metadata:
      overrides && overrides.hasOwnProperty('metadata')
        ? overrides.metadata!
        : [
            buildMetadataItemDefinition(),
            buildMetadataItemDefinition(),
            buildMetadataItemDefinition(),
          ],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'iure',
    outputDefinitions:
      overrides && overrides.hasOwnProperty('outputDefinitions')
        ? overrides.outputDefinitions!
        : [buildOutputDefinition(), buildOutputDefinition(), buildOutputDefinition()],
  };
};

export const buildInput = (
  overrides?: Partial<Types.Input>,
): {__typename: 'Input'} & Types.Input => {
  return {
    __typename: 'Input',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : buildInputDefinition(),
    dependsOn:
      overrides && overrides.hasOwnProperty('dependsOn')
        ? overrides.dependsOn!
        : [buildOutput(), buildOutput(), buildOutput()],
    isDynamicCollect:
      overrides && overrides.hasOwnProperty('isDynamicCollect')
        ? overrides.isDynamicCollect!
        : false,
    solid: overrides && overrides.hasOwnProperty('solid') ? overrides.solid! : buildSolid(),
  };
};

export const buildInputDefinition = (
  overrides?: Partial<Types.InputDefinition>,
): {__typename: 'InputDefinition'} & Types.InputDefinition => {
  return {
    __typename: 'InputDefinition',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'iusto',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'non',
    solidDefinition:
      overrides && overrides.hasOwnProperty('solidDefinition')
        ? overrides.solidDefinition!
        : buildSolidDefinition(),
    type: overrides && overrides.hasOwnProperty('type') ? overrides.type! : buildDagsterType(),
  };
};

export const buildInputMapping = (
  overrides?: Partial<Types.InputMapping>,
): {__typename: 'InputMapping'} & Types.InputMapping => {
  return {
    __typename: 'InputMapping',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : buildInputDefinition(),
    mappedInput:
      overrides && overrides.hasOwnProperty('mappedInput') ? overrides.mappedInput! : buildInput(),
  };
};

export const buildInputTag = (overrides?: Partial<Types.InputTag>): Types.InputTag => {
  return {
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'possimus',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'quod',
  };
};

export const buildInstance = (
  overrides?: Partial<Types.Instance>,
): {__typename: 'Instance'} & Types.Instance => {
  return {
    __typename: 'Instance',
    daemonHealth:
      overrides && overrides.hasOwnProperty('daemonHealth')
        ? overrides.daemonHealth!
        : buildDaemonHealth(),
    executablePath:
      overrides && overrides.hasOwnProperty('executablePath') ? overrides.executablePath! : 'fuga',
    hasCapturedLogManager:
      overrides && overrides.hasOwnProperty('hasCapturedLogManager')
        ? overrides.hasCapturedLogManager!
        : true,
    hasInfo: overrides && overrides.hasOwnProperty('hasInfo') ? overrides.hasInfo! : true,
    info: overrides && overrides.hasOwnProperty('info') ? overrides.info! : 'qui',
    runLauncher:
      overrides && overrides.hasOwnProperty('runLauncher')
        ? overrides.runLauncher!
        : buildRunLauncher(),
    runQueuingSupported:
      overrides && overrides.hasOwnProperty('runQueuingSupported')
        ? overrides.runQueuingSupported!
        : true,
  };
};

export const buildInstigationEvent = (
  overrides?: Partial<Types.InstigationEvent>,
): {__typename: 'InstigationEvent'} & Types.InstigationEvent => {
  return {
    __typename: 'InstigationEvent',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ea',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'architecto',
  };
};

export const buildInstigationEventConnection = (
  overrides?: Partial<Types.InstigationEventConnection>,
): {__typename: 'InstigationEventConnection'} & Types.InstigationEventConnection => {
  return {
    __typename: 'InstigationEventConnection',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'harum',
    events:
      overrides && overrides.hasOwnProperty('events')
        ? overrides.events!
        : [buildInstigationEvent(), buildInstigationEvent(), buildInstigationEvent()],
    hasMore: overrides && overrides.hasOwnProperty('hasMore') ? overrides.hasMore! : true,
  };
};

export const buildInstigationSelector = (
  overrides?: Partial<Types.InstigationSelector>,
): Types.InstigationSelector => {
  return {
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'et',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'unde',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName')
        ? overrides.repositoryName!
        : 'facere',
  };
};

export const buildInstigationState = (
  overrides?: Partial<Types.InstigationState>,
): {__typename: 'InstigationState'} & Types.InstigationState => {
  return {
    __typename: 'InstigationState',
    hasStartPermission:
      overrides && overrides.hasOwnProperty('hasStartPermission')
        ? overrides.hasStartPermission!
        : false,
    hasStopPermission:
      overrides && overrides.hasOwnProperty('hasStopPermission')
        ? overrides.hasStopPermission!
        : false,
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'd5982bfb-a8c4-4fe2-962e-f57653e1753b',
    instigationType:
      overrides && overrides.hasOwnProperty('instigationType')
        ? overrides.instigationType!
        : Types.InstigationType.Schedule,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'praesentium',
    nextTick:
      overrides && overrides.hasOwnProperty('nextTick')
        ? overrides.nextTick!
        : buildDryRunInstigationTick(),
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'omnis',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'non',
    repositoryOrigin:
      overrides && overrides.hasOwnProperty('repositoryOrigin')
        ? overrides.repositoryOrigin!
        : buildRepositoryOrigin(),
    runningCount:
      overrides && overrides.hasOwnProperty('runningCount') ? overrides.runningCount! : 6523,
    runs:
      overrides && overrides.hasOwnProperty('runs')
        ? overrides.runs!
        : [buildRun(), buildRun(), buildRun()],
    runsCount: overrides && overrides.hasOwnProperty('runsCount') ? overrides.runsCount! : 6663,
    selectorId: overrides && overrides.hasOwnProperty('selectorId') ? overrides.selectorId! : 'aut',
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.InstigationStatus.Running,
    tick: overrides && overrides.hasOwnProperty('tick') ? overrides.tick! : buildInstigationTick(),
    ticks:
      overrides && overrides.hasOwnProperty('ticks')
        ? overrides.ticks!
        : [buildInstigationTick(), buildInstigationTick(), buildInstigationTick()],
    typeSpecificData:
      overrides && overrides.hasOwnProperty('typeSpecificData')
        ? overrides.typeSpecificData!
        : buildScheduleData(),
  };
};

export const buildInstigationStateNotFoundError = (
  overrides?: Partial<Types.InstigationStateNotFoundError>,
): {__typename: 'InstigationStateNotFoundError'} & Types.InstigationStateNotFoundError => {
  return {
    __typename: 'InstigationStateNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'nihil',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'fuga',
  };
};

export const buildInstigationStates = (
  overrides?: Partial<Types.InstigationStates>,
): {__typename: 'InstigationStates'} & Types.InstigationStates => {
  return {
    __typename: 'InstigationStates',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildInstigationState(), buildInstigationState(), buildInstigationState()],
  };
};

export const buildInstigationTick = (
  overrides?: Partial<Types.InstigationTick>,
): {__typename: 'InstigationTick'} & Types.InstigationTick => {
  return {
    __typename: 'InstigationTick',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'voluptatem',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'd7be0ce0-364e-498b-98ec-cc8b0f746723',
    logEvents:
      overrides && overrides.hasOwnProperty('logEvents')
        ? overrides.logEvents!
        : buildInstigationEventConnection(),
    logKey:
      overrides && overrides.hasOwnProperty('logKey')
        ? overrides.logKey!
        : ['occaecati', 'eveniet', 'consequatur'],
    originRunIds:
      overrides && overrides.hasOwnProperty('originRunIds')
        ? overrides.originRunIds!
        : ['fuga', 'aliquid', 'neque'],
    runIds:
      overrides && overrides.hasOwnProperty('runIds')
        ? overrides.runIds!
        : ['blanditiis', 'cupiditate', 'aut'],
    runKeys:
      overrides && overrides.hasOwnProperty('runKeys')
        ? overrides.runKeys!
        : ['nisi', 'est', 'accusamus'],
    runs:
      overrides && overrides.hasOwnProperty('runs')
        ? overrides.runs!
        : [buildRun(), buildRun(), buildRun()],
    skipReason:
      overrides && overrides.hasOwnProperty('skipReason') ? overrides.skipReason! : 'maxime',
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.InstigationTickStatus.Failure,
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 6.06,
  };
};

export const buildIntMetadataEntry = (
  overrides?: Partial<Types.IntMetadataEntry>,
): {__typename: 'IntMetadataEntry'} & Types.IntMetadataEntry => {
  return {
    __typename: 'IntMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'et',
    intRepr: overrides && overrides.hasOwnProperty('intRepr') ? overrides.intRepr! : 'omnis',
    intValue: overrides && overrides.hasOwnProperty('intValue') ? overrides.intValue! : 9039,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'enim',
  };
};

export const buildInvalidOutputError = (
  overrides?: Partial<Types.InvalidOutputError>,
): {__typename: 'InvalidOutputError'} & Types.InvalidOutputError => {
  return {
    __typename: 'InvalidOutputError',
    invalidOutputName:
      overrides && overrides.hasOwnProperty('invalidOutputName')
        ? overrides.invalidOutputName!
        : 'commodi',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'et',
  };
};

export const buildInvalidPipelineRunsFilterError = (
  overrides?: Partial<Types.InvalidPipelineRunsFilterError>,
): {__typename: 'InvalidPipelineRunsFilterError'} & Types.InvalidPipelineRunsFilterError => {
  return {
    __typename: 'InvalidPipelineRunsFilterError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
  };
};

export const buildInvalidStepError = (
  overrides?: Partial<Types.InvalidStepError>,
): {__typename: 'InvalidStepError'} & Types.InvalidStepError => {
  return {
    __typename: 'InvalidStepError',
    invalidStepKey:
      overrides && overrides.hasOwnProperty('invalidStepKey')
        ? overrides.invalidStepKey!
        : 'doloribus',
  };
};

export const buildInvalidSubsetError = (
  overrides?: Partial<Types.InvalidSubsetError>,
): {__typename: 'InvalidSubsetError'} & Types.InvalidSubsetError => {
  return {
    __typename: 'InvalidSubsetError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'aut',
    pipeline:
      overrides && overrides.hasOwnProperty('pipeline') ? overrides.pipeline! : buildPipeline(),
  };
};

export const buildJob = (overrides?: Partial<Types.Job>): {__typename: 'Job'} & Types.Job => {
  return {
    __typename: 'Job',
    dagsterTypeOrError:
      overrides && overrides.hasOwnProperty('dagsterTypeOrError')
        ? overrides.dagsterTypeOrError!
        : buildDagsterTypeNotFoundError(),
    dagsterTypes:
      overrides && overrides.hasOwnProperty('dagsterTypes')
        ? overrides.dagsterTypes!
        : [buildDagsterType(), buildDagsterType(), buildDagsterType()],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'occaecati',
    graphName:
      overrides && overrides.hasOwnProperty('graphName') ? overrides.graphName! : 'eveniet',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'f1c0de0d-2ab7-40ab-8344-a0f76da09d78',
    isAssetJob: overrides && overrides.hasOwnProperty('isAssetJob') ? overrides.isAssetJob! : false,
    isJob: overrides && overrides.hasOwnProperty('isJob') ? overrides.isJob! : true,
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    modes:
      overrides && overrides.hasOwnProperty('modes')
        ? overrides.modes!
        : [buildMode(), buildMode(), buildMode()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'rerum',
    parentSnapshotId:
      overrides && overrides.hasOwnProperty('parentSnapshotId')
        ? overrides.parentSnapshotId!
        : 'tempore',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'maxime',
    presets:
      overrides && overrides.hasOwnProperty('presets')
        ? overrides.presets!
        : [buildPipelinePreset(), buildPipelinePreset(), buildPipelinePreset()],
    repository:
      overrides && overrides.hasOwnProperty('repository')
        ? overrides.repository!
        : buildRepository(),
    runs:
      overrides && overrides.hasOwnProperty('runs')
        ? overrides.runs!
        : [buildRun(), buildRun(), buildRun()],
    schedules:
      overrides && overrides.hasOwnProperty('schedules')
        ? overrides.schedules!
        : [buildSchedule(), buildSchedule(), buildSchedule()],
    sensors:
      overrides && overrides.hasOwnProperty('sensors')
        ? overrides.sensors!
        : [buildSensor(), buildSensor(), buildSensor()],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : buildSolidHandle(),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles')
        ? overrides.solidHandles!
        : [buildSolidHandle(), buildSolidHandle(), buildSolidHandle()],
    solids:
      overrides && overrides.hasOwnProperty('solids')
        ? overrides.solids!
        : [buildSolid(), buildSolid(), buildSolid()],
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildPipelineTag(), buildPipelineTag(), buildPipelineTag()],
  };
};

export const buildJobOrPipelineSelector = (
  overrides?: Partial<Types.JobOrPipelineSelector>,
): Types.JobOrPipelineSelector => {
  return {
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection')
        ? overrides.assetSelection!
        : [buildAssetKeyInput(), buildAssetKeyInput(), buildAssetKeyInput()],
    jobName: overrides && overrides.hasOwnProperty('jobName') ? overrides.jobName! : 'quia',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'accusantium',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'aut',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'velit',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['libero', 'rerum', 'qui'],
  };
};

export const buildJsonMetadataEntry = (
  overrides?: Partial<Types.JsonMetadataEntry>,
): {__typename: 'JsonMetadataEntry'} & Types.JsonMetadataEntry => {
  return {
    __typename: 'JsonMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'et',
    jsonString: overrides && overrides.hasOwnProperty('jsonString') ? overrides.jsonString! : 'qui',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'ut',
  };
};

export const buildLaunchBackfillMutation = (
  overrides?: Partial<Types.LaunchBackfillMutation>,
): {__typename: 'LaunchBackfillMutation'} & Types.LaunchBackfillMutation => {
  return {
    __typename: 'LaunchBackfillMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : buildConflictingExecutionParamsError(),
  };
};

export const buildLaunchBackfillParams = (
  overrides?: Partial<Types.LaunchBackfillParams>,
): Types.LaunchBackfillParams => {
  return {
    allPartitions:
      overrides && overrides.hasOwnProperty('allPartitions') ? overrides.allPartitions! : false,
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection')
        ? overrides.assetSelection!
        : [buildAssetKeyInput(), buildAssetKeyInput(), buildAssetKeyInput()],
    forceSynchronousSubmission:
      overrides && overrides.hasOwnProperty('forceSynchronousSubmission')
        ? overrides.forceSynchronousSubmission!
        : true,
    fromFailure:
      overrides && overrides.hasOwnProperty('fromFailure') ? overrides.fromFailure! : true,
    partitionNames:
      overrides && overrides.hasOwnProperty('partitionNames')
        ? overrides.partitionNames!
        : ['nesciunt', 'et', 'quia'],
    reexecutionSteps:
      overrides && overrides.hasOwnProperty('reexecutionSteps')
        ? overrides.reexecutionSteps!
        : ['excepturi', 'culpa', 'qui'],
    selector:
      overrides && overrides.hasOwnProperty('selector')
        ? overrides.selector!
        : buildPartitionSetSelector(),
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildExecutionTag(), buildExecutionTag(), buildExecutionTag()],
  };
};

export const buildLaunchBackfillSuccess = (
  overrides?: Partial<Types.LaunchBackfillSuccess>,
): {__typename: 'LaunchBackfillSuccess'} & Types.LaunchBackfillSuccess => {
  return {
    __typename: 'LaunchBackfillSuccess',
    backfillId: overrides && overrides.hasOwnProperty('backfillId') ? overrides.backfillId! : 'sit',
    launchedRunIds:
      overrides && overrides.hasOwnProperty('launchedRunIds')
        ? overrides.launchedRunIds!
        : ['eos', 'eos', 'quis'],
  };
};

export const buildLaunchPipelineRunSuccess = (
  overrides?: Partial<Types.LaunchPipelineRunSuccess>,
): {__typename: 'LaunchPipelineRunSuccess'} & Types.LaunchPipelineRunSuccess => {
  return {
    __typename: 'LaunchPipelineRunSuccess',
    run: overrides && overrides.hasOwnProperty('run') ? overrides.run! : buildRun(),
  };
};

export const buildLaunchRunMutation = (
  overrides?: Partial<Types.LaunchRunMutation>,
): {__typename: 'LaunchRunMutation'} & Types.LaunchRunMutation => {
  return {
    __typename: 'LaunchRunMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : buildConflictingExecutionParamsError(),
  };
};

export const buildLaunchRunReexecutionMutation = (
  overrides?: Partial<Types.LaunchRunReexecutionMutation>,
): {__typename: 'LaunchRunReexecutionMutation'} & Types.LaunchRunReexecutionMutation => {
  return {
    __typename: 'LaunchRunReexecutionMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : buildConflictingExecutionParamsError(),
  };
};

export const buildLaunchRunSuccess = (
  overrides?: Partial<Types.LaunchRunSuccess>,
): {__typename: 'LaunchRunSuccess'} & Types.LaunchRunSuccess => {
  return {
    __typename: 'LaunchRunSuccess',
    run: overrides && overrides.hasOwnProperty('run') ? overrides.run! : buildRun(),
  };
};

export const buildListDagsterType = (
  overrides?: Partial<Types.ListDagsterType>,
): {__typename: 'ListDagsterType'} & Types.ListDagsterType => {
  return {
    __typename: 'ListDagsterType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'enim',
    displayName:
      overrides && overrides.hasOwnProperty('displayName') ? overrides.displayName! : 'soluta',
    innerTypes:
      overrides && overrides.hasOwnProperty('innerTypes')
        ? overrides.innerTypes!
        : [buildDagsterType(), buildDagsterType(), buildDagsterType()],
    inputSchemaType:
      overrides && overrides.hasOwnProperty('inputSchemaType')
        ? overrides.inputSchemaType!
        : buildConfigType(),
    isBuiltin: overrides && overrides.hasOwnProperty('isBuiltin') ? overrides.isBuiltin! : true,
    isList: overrides && overrides.hasOwnProperty('isList') ? overrides.isList! : true,
    isNothing: overrides && overrides.hasOwnProperty('isNothing') ? overrides.isNothing! : true,
    isNullable: overrides && overrides.hasOwnProperty('isNullable') ? overrides.isNullable! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'aut',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'culpa',
    ofType:
      overrides && overrides.hasOwnProperty('ofType') ? overrides.ofType! : buildDagsterType(),
    outputSchemaType:
      overrides && overrides.hasOwnProperty('outputSchemaType')
        ? overrides.outputSchemaType!
        : buildConfigType(),
  };
};

export const buildLoadedInputEvent = (
  overrides?: Partial<Types.LoadedInputEvent>,
): {__typename: 'LoadedInputEvent'} & Types.LoadedInputEvent => {
  return {
    __typename: 'LoadedInputEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'impedit',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    inputName: overrides && overrides.hasOwnProperty('inputName') ? overrides.inputName! : 'quia',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'facere',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    managerKey:
      overrides && overrides.hasOwnProperty('managerKey') ? overrides.managerKey! : 'quae',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'eveniet',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'porro',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'qui',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'et',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'ut',
    upstreamOutputName:
      overrides && overrides.hasOwnProperty('upstreamOutputName')
        ? overrides.upstreamOutputName!
        : 'sed',
    upstreamStepKey:
      overrides && overrides.hasOwnProperty('upstreamStepKey')
        ? overrides.upstreamStepKey!
        : 'debitis',
  };
};

export const buildLocationStateChangeEvent = (
  overrides?: Partial<Types.LocationStateChangeEvent>,
): {__typename: 'LocationStateChangeEvent'} & Types.LocationStateChangeEvent => {
  return {
    __typename: 'LocationStateChangeEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.LocationStateChangeEventType.LocationDisconnected,
    locationName:
      overrides && overrides.hasOwnProperty('locationName') ? overrides.locationName! : 'tempora',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'at',
    serverId: overrides && overrides.hasOwnProperty('serverId') ? overrides.serverId! : 'adipisci',
  };
};

export const buildLocationStateChangeSubscription = (
  overrides?: Partial<Types.LocationStateChangeSubscription>,
): {__typename: 'LocationStateChangeSubscription'} & Types.LocationStateChangeSubscription => {
  return {
    __typename: 'LocationStateChangeSubscription',
    event:
      overrides && overrides.hasOwnProperty('event')
        ? overrides.event!
        : buildLocationStateChangeEvent(),
  };
};

export const buildLogMessageEvent = (
  overrides?: Partial<Types.LogMessageEvent>,
): {__typename: 'LogMessageEvent'} & Types.LogMessageEvent => {
  return {
    __typename: 'LogMessageEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'officiis',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'laboriosam',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'error',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'voluptatibus',
  };
};

export const buildLogTelemetrySuccess = (
  overrides?: Partial<Types.LogTelemetrySuccess>,
): {__typename: 'LogTelemetrySuccess'} & Types.LogTelemetrySuccess => {
  return {
    __typename: 'LogTelemetrySuccess',
    action: overrides && overrides.hasOwnProperty('action') ? overrides.action! : 'assumenda',
  };
};

export const buildLogger = (
  overrides?: Partial<Types.Logger>,
): {__typename: 'Logger'} & Types.Logger => {
  return {
    __typename: 'Logger',
    configField:
      overrides && overrides.hasOwnProperty('configField')
        ? overrides.configField!
        : buildConfigTypeField(),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'non',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'quas',
  };
};

export const buildLogsCapturedEvent = (
  overrides?: Partial<Types.LogsCapturedEvent>,
): {__typename: 'LogsCapturedEvent'} & Types.LogsCapturedEvent => {
  return {
    __typename: 'LogsCapturedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    externalUrl:
      overrides && overrides.hasOwnProperty('externalUrl') ? overrides.externalUrl! : 'qui',
    fileKey: overrides && overrides.hasOwnProperty('fileKey') ? overrides.fileKey! : 'et',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    logKey: overrides && overrides.hasOwnProperty('logKey') ? overrides.logKey! : 'fuga',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ex',
    pid: overrides && overrides.hasOwnProperty('pid') ? overrides.pid! : 7623,
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'modi',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'assumenda',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'quia',
    stepKeys:
      overrides && overrides.hasOwnProperty('stepKeys')
        ? overrides.stepKeys!
        : ['magni', 'autem', 'voluptas'],
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'et',
  };
};

export const buildMapConfigType = (
  overrides?: Partial<Types.MapConfigType>,
): {__typename: 'MapConfigType'} & Types.MapConfigType => {
  return {
    __typename: 'MapConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quis',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'temporibus',
    keyLabelName:
      overrides && overrides.hasOwnProperty('keyLabelName') ? overrides.keyLabelName! : 'nostrum',
    keyType:
      overrides && overrides.hasOwnProperty('keyType') ? overrides.keyType! : buildConfigType(),
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [buildConfigType(), buildConfigType(), buildConfigType()],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys')
        ? overrides.typeParamKeys!
        : ['impedit', 'unde', 'natus'],
    valueType:
      overrides && overrides.hasOwnProperty('valueType') ? overrides.valueType! : buildConfigType(),
  };
};

export const buildMarkdownMetadataEntry = (
  overrides?: Partial<Types.MarkdownMetadataEntry>,
): {__typename: 'MarkdownMetadataEntry'} & Types.MarkdownMetadataEntry => {
  return {
    __typename: 'MarkdownMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'eum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'nam',
    mdStr: overrides && overrides.hasOwnProperty('mdStr') ? overrides.mdStr! : 'quia',
  };
};

export const buildMarkerEvent = (
  overrides?: Partial<Types.MarkerEvent>,
): {__typename: 'MarkerEvent'} & Types.MarkerEvent => {
  return {
    __typename: 'MarkerEvent',
    markerEnd:
      overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'voluptas',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'ut',
  };
};

export const buildMarshalledInput = (
  overrides?: Partial<Types.MarshalledInput>,
): Types.MarshalledInput => {
  return {
    inputName: overrides && overrides.hasOwnProperty('inputName') ? overrides.inputName! : 'nobis',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'nam',
  };
};

export const buildMarshalledOutput = (
  overrides?: Partial<Types.MarshalledOutput>,
): Types.MarshalledOutput => {
  return {
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'sed',
    outputName:
      overrides && overrides.hasOwnProperty('outputName') ? overrides.outputName! : 'inventore',
  };
};

export const buildMaterializationEvent = (
  overrides?: Partial<Types.MaterializationEvent>,
): {__typename: 'MaterializationEvent'} & Types.MaterializationEvent => {
  return {
    __typename: 'MaterializationEvent',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey') ? overrides.assetKey! : buildAssetKey(),
    assetLineage:
      overrides && overrides.hasOwnProperty('assetLineage')
        ? overrides.assetLineage!
        : [buildAssetLineageInfo(), buildAssetLineageInfo(), buildAssetLineageInfo()],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'eaque',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'possimus',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'voluptatem',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    partition: overrides && overrides.hasOwnProperty('partition') ? overrides.partition! : 'velit',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'velit',
    runOrError:
      overrides && overrides.hasOwnProperty('runOrError')
        ? overrides.runOrError!
        : buildPythonError(),
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'qui',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'ratione',
    stepStats:
      overrides && overrides.hasOwnProperty('stepStats')
        ? overrides.stepStats!
        : buildRunStepStats(),
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildEventTag(), buildEventTag(), buildEventTag()],
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'id',
  };
};

export const buildMaterializationUpstreamDataVersion = (
  overrides?: Partial<Types.MaterializationUpstreamDataVersion>,
): {
  __typename: 'MaterializationUpstreamDataVersion';
} & Types.MaterializationUpstreamDataVersion => {
  return {
    __typename: 'MaterializationUpstreamDataVersion',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey') ? overrides.assetKey! : buildAssetKey(),
    downstreamAssetKey:
      overrides && overrides.hasOwnProperty('downstreamAssetKey')
        ? overrides.downstreamAssetKey!
        : buildAssetKey(),
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'aut',
  };
};

export const buildMaterializedPartitionRange2D = (
  overrides?: Partial<Types.MaterializedPartitionRange2D>,
): {__typename: 'MaterializedPartitionRange2D'} & Types.MaterializedPartitionRange2D => {
  return {
    __typename: 'MaterializedPartitionRange2D',
    primaryDimEndKey:
      overrides && overrides.hasOwnProperty('primaryDimEndKey')
        ? overrides.primaryDimEndKey!
        : 'et',
    primaryDimEndTime:
      overrides && overrides.hasOwnProperty('primaryDimEndTime')
        ? overrides.primaryDimEndTime!
        : 9.29,
    primaryDimStartKey:
      overrides && overrides.hasOwnProperty('primaryDimStartKey')
        ? overrides.primaryDimStartKey!
        : 'repudiandae',
    primaryDimStartTime:
      overrides && overrides.hasOwnProperty('primaryDimStartTime')
        ? overrides.primaryDimStartTime!
        : 9.31,
    secondaryDim:
      overrides && overrides.hasOwnProperty('secondaryDim')
        ? overrides.secondaryDim!
        : buildDefaultPartitions(),
  };
};

export const buildMessageEvent = (
  overrides?: Partial<Types.MessageEvent>,
): {__typename: 'MessageEvent'} & Types.MessageEvent => {
  return {
    __typename: 'MessageEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'tenetur',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'numquam',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'doloribus',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'dolore',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'qui',
  };
};

export const buildMetadataEntry = (
  overrides?: Partial<Types.MetadataEntry>,
): {__typename: 'MetadataEntry'} & Types.MetadataEntry => {
  return {
    __typename: 'MetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'laborum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'aut',
  };
};

export const buildMetadataItemDefinition = (
  overrides?: Partial<Types.MetadataItemDefinition>,
): {__typename: 'MetadataItemDefinition'} & Types.MetadataItemDefinition => {
  return {
    __typename: 'MetadataItemDefinition',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'ex',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'quasi',
  };
};

export const buildMissingFieldConfigError = (
  overrides?: Partial<Types.MissingFieldConfigError>,
): {__typename: 'MissingFieldConfigError'} & Types.MissingFieldConfigError => {
  return {
    __typename: 'MissingFieldConfigError',
    field:
      overrides && overrides.hasOwnProperty('field') ? overrides.field! : buildConfigTypeField(),
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'autem',
    path:
      overrides && overrides.hasOwnProperty('path')
        ? overrides.path!
        : ['aut', 'sunt', 'voluptatem'],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : Types.EvaluationErrorReason.FieldsNotDefined,
    stack:
      overrides && overrides.hasOwnProperty('stack') ? overrides.stack! : buildEvaluationStack(),
  };
};

export const buildMissingFieldsConfigError = (
  overrides?: Partial<Types.MissingFieldsConfigError>,
): {__typename: 'MissingFieldsConfigError'} & Types.MissingFieldsConfigError => {
  return {
    __typename: 'MissingFieldsConfigError',
    fields:
      overrides && overrides.hasOwnProperty('fields')
        ? overrides.fields!
        : [buildConfigTypeField(), buildConfigTypeField(), buildConfigTypeField()],
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'voluptatibus',
    path:
      overrides && overrides.hasOwnProperty('path')
        ? overrides.path!
        : ['accusantium', 'omnis', 'autem'],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : Types.EvaluationErrorReason.FieldsNotDefined,
    stack:
      overrides && overrides.hasOwnProperty('stack') ? overrides.stack! : buildEvaluationStack(),
  };
};

export const buildMissingRunIdErrorEvent = (
  overrides?: Partial<Types.MissingRunIdErrorEvent>,
): {__typename: 'MissingRunIdErrorEvent'} & Types.MissingRunIdErrorEvent => {
  return {
    __typename: 'MissingRunIdErrorEvent',
    invalidRunId:
      overrides && overrides.hasOwnProperty('invalidRunId') ? overrides.invalidRunId! : 'quis',
  };
};

export const buildMode = (overrides?: Partial<Types.Mode>): {__typename: 'Mode'} & Types.Mode => {
  return {
    __typename: 'Mode',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'dolor',
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'quia',
    loggers:
      overrides && overrides.hasOwnProperty('loggers')
        ? overrides.loggers!
        : [buildLogger(), buildLogger(), buildLogger()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'aliquam',
    resources:
      overrides && overrides.hasOwnProperty('resources')
        ? overrides.resources!
        : [buildResource(), buildResource(), buildResource()],
  };
};

export const buildModeNotFoundError = (
  overrides?: Partial<Types.ModeNotFoundError>,
): {__typename: 'ModeNotFoundError'} & Types.ModeNotFoundError => {
  return {
    __typename: 'ModeNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'eius',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'dolorem',
  };
};

export const buildMultiPartitions = (
  overrides?: Partial<Types.MultiPartitions>,
): {__typename: 'MultiPartitions'} & Types.MultiPartitions => {
  return {
    __typename: 'MultiPartitions',
    primaryDimensionName:
      overrides && overrides.hasOwnProperty('primaryDimensionName')
        ? overrides.primaryDimensionName!
        : 'consequatur',
    ranges:
      overrides && overrides.hasOwnProperty('ranges')
        ? overrides.ranges!
        : [
            buildMaterializedPartitionRange2D(),
            buildMaterializedPartitionRange2D(),
            buildMaterializedPartitionRange2D(),
          ],
  };
};

export const buildNoModeProvidedError = (
  overrides?: Partial<Types.NoModeProvidedError>,
): {__typename: 'NoModeProvidedError'} & Types.NoModeProvidedError => {
  return {
    __typename: 'NoModeProvidedError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'neque',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'quidem',
  };
};

export const buildNodeInvocationSite = (
  overrides?: Partial<Types.NodeInvocationSite>,
): {__typename: 'NodeInvocationSite'} & Types.NodeInvocationSite => {
  return {
    __typename: 'NodeInvocationSite',
    pipeline:
      overrides && overrides.hasOwnProperty('pipeline') ? overrides.pipeline! : buildPipeline(),
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : buildSolidHandle(),
  };
};

export const buildNotebookMetadataEntry = (
  overrides?: Partial<Types.NotebookMetadataEntry>,
): {__typename: 'NotebookMetadataEntry'} & Types.NotebookMetadataEntry => {
  return {
    __typename: 'NotebookMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quis',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'aut',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : 'reprehenderit',
  };
};

export const buildNullMetadataEntry = (
  overrides?: Partial<Types.NullMetadataEntry>,
): {__typename: 'NullMetadataEntry'} & Types.NullMetadataEntry => {
  return {
    __typename: 'NullMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'molestias',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'dolorem',
  };
};

export const buildNullableConfigType = (
  overrides?: Partial<Types.NullableConfigType>,
): {__typename: 'NullableConfigType'} & Types.NullableConfigType => {
  return {
    __typename: 'NullableConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'voluptas',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'consequuntur',
    ofType: overrides && overrides.hasOwnProperty('ofType') ? overrides.ofType! : buildConfigType(),
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [buildConfigType(), buildConfigType(), buildConfigType()],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys')
        ? overrides.typeParamKeys!
        : ['incidunt', 'sint', 'qui'],
  };
};

export const buildNullableDagsterType = (
  overrides?: Partial<Types.NullableDagsterType>,
): {__typename: 'NullableDagsterType'} & Types.NullableDagsterType => {
  return {
    __typename: 'NullableDagsterType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'ea',
    displayName:
      overrides && overrides.hasOwnProperty('displayName')
        ? overrides.displayName!
        : 'necessitatibus',
    innerTypes:
      overrides && overrides.hasOwnProperty('innerTypes')
        ? overrides.innerTypes!
        : [buildDagsterType(), buildDagsterType(), buildDagsterType()],
    inputSchemaType:
      overrides && overrides.hasOwnProperty('inputSchemaType')
        ? overrides.inputSchemaType!
        : buildConfigType(),
    isBuiltin: overrides && overrides.hasOwnProperty('isBuiltin') ? overrides.isBuiltin! : false,
    isList: overrides && overrides.hasOwnProperty('isList') ? overrides.isList! : false,
    isNothing: overrides && overrides.hasOwnProperty('isNothing') ? overrides.isNothing! : true,
    isNullable: overrides && overrides.hasOwnProperty('isNullable') ? overrides.isNullable! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'perferendis',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'nulla',
    ofType:
      overrides && overrides.hasOwnProperty('ofType') ? overrides.ofType! : buildDagsterType(),
    outputSchemaType:
      overrides && overrides.hasOwnProperty('outputSchemaType')
        ? overrides.outputSchemaType!
        : buildConfigType(),
  };
};

export const buildObjectStoreOperationEvent = (
  overrides?: Partial<Types.ObjectStoreOperationEvent>,
): {__typename: 'ObjectStoreOperationEvent'} & Types.ObjectStoreOperationEvent => {
  return {
    __typename: 'ObjectStoreOperationEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
    operationResult:
      overrides && overrides.hasOwnProperty('operationResult')
        ? overrides.operationResult!
        : buildObjectStoreOperationResult(),
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'vero',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'repellendus',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'et',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'amet',
  };
};

export const buildObjectStoreOperationResult = (
  overrides?: Partial<Types.ObjectStoreOperationResult>,
): {__typename: 'ObjectStoreOperationResult'} & Types.ObjectStoreOperationResult => {
  return {
    __typename: 'ObjectStoreOperationResult',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'porro',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'nobis',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    op:
      overrides && overrides.hasOwnProperty('op')
        ? overrides.op!
        : Types.ObjectStoreOperationType.CpObject,
  };
};

export const buildObservationEvent = (
  overrides?: Partial<Types.ObservationEvent>,
): {__typename: 'ObservationEvent'} & Types.ObservationEvent => {
  return {
    __typename: 'ObservationEvent',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey') ? overrides.assetKey! : buildAssetKey(),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'dolorum',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'non',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ratione',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    partition: overrides && overrides.hasOwnProperty('partition') ? overrides.partition! : 'esse',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'aliquid',
    runOrError:
      overrides && overrides.hasOwnProperty('runOrError')
        ? overrides.runOrError!
        : buildPythonError(),
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'possimus',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'magnam',
    stepStats:
      overrides && overrides.hasOwnProperty('stepStats')
        ? overrides.stepStats!
        : buildRunStepStats(),
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildEventTag(), buildEventTag(), buildEventTag()],
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'ut',
  };
};

export const buildOutput = (
  overrides?: Partial<Types.Output>,
): {__typename: 'Output'} & Types.Output => {
  return {
    __typename: 'Output',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : buildOutputDefinition(),
    dependedBy:
      overrides && overrides.hasOwnProperty('dependedBy')
        ? overrides.dependedBy!
        : [buildInput(), buildInput(), buildInput()],
    solid: overrides && overrides.hasOwnProperty('solid') ? overrides.solid! : buildSolid(),
  };
};

export const buildOutputDefinition = (
  overrides?: Partial<Types.OutputDefinition>,
): {__typename: 'OutputDefinition'} & Types.OutputDefinition => {
  return {
    __typename: 'OutputDefinition',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quis',
    isDynamic: overrides && overrides.hasOwnProperty('isDynamic') ? overrides.isDynamic! : false,
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'repellendus',
    solidDefinition:
      overrides && overrides.hasOwnProperty('solidDefinition')
        ? overrides.solidDefinition!
        : buildSolidDefinition(),
    type: overrides && overrides.hasOwnProperty('type') ? overrides.type! : buildDagsterType(),
  };
};

export const buildOutputMapping = (
  overrides?: Partial<Types.OutputMapping>,
): {__typename: 'OutputMapping'} & Types.OutputMapping => {
  return {
    __typename: 'OutputMapping',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : buildOutputDefinition(),
    mappedOutput:
      overrides && overrides.hasOwnProperty('mappedOutput')
        ? overrides.mappedOutput!
        : buildOutput(),
  };
};

export const buildPartition = (
  overrides?: Partial<Types.Partition>,
): {__typename: 'Partition'} & Types.Partition => {
  return {
    __typename: 'Partition',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'eum',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'quam',
    partitionSetName:
      overrides && overrides.hasOwnProperty('partitionSetName')
        ? overrides.partitionSetName!
        : 'voluptatum',
    runConfigOrError:
      overrides && overrides.hasOwnProperty('runConfigOrError')
        ? overrides.runConfigOrError!
        : buildPartitionRunConfig(),
    runs:
      overrides && overrides.hasOwnProperty('runs')
        ? overrides.runs!
        : [buildRun(), buildRun(), buildRun()],
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['et', 'soluta', 'quasi'],
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.RunStatus.Canceled,
    tagsOrError:
      overrides && overrides.hasOwnProperty('tagsOrError')
        ? overrides.tagsOrError!
        : buildPartitionTags(),
  };
};

export const buildPartitionBackfill = (
  overrides?: Partial<Types.PartitionBackfill>,
): {__typename: 'PartitionBackfill'} & Types.PartitionBackfill => {
  return {
    __typename: 'PartitionBackfill',
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection')
        ? overrides.assetSelection!
        : [buildAssetKey(), buildAssetKey(), buildAssetKey()],
    backfillId:
      overrides && overrides.hasOwnProperty('backfillId') ? overrides.backfillId! : 'sint',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    fromFailure:
      overrides && overrides.hasOwnProperty('fromFailure') ? overrides.fromFailure! : true,
    hasCancelPermission:
      overrides && overrides.hasOwnProperty('hasCancelPermission')
        ? overrides.hasCancelPermission!
        : false,
    hasResumePermission:
      overrides && overrides.hasOwnProperty('hasResumePermission')
        ? overrides.hasResumePermission!
        : true,
    isValidSerialization:
      overrides && overrides.hasOwnProperty('isValidSerialization')
        ? overrides.isValidSerialization!
        : false,
    numCancelable:
      overrides && overrides.hasOwnProperty('numCancelable') ? overrides.numCancelable! : 53,
    numPartitions:
      overrides && overrides.hasOwnProperty('numPartitions') ? overrides.numPartitions! : 4165,
    partitionNames:
      overrides && overrides.hasOwnProperty('partitionNames')
        ? overrides.partitionNames!
        : ['et', 'architecto', 'sed'],
    partitionSet:
      overrides && overrides.hasOwnProperty('partitionSet')
        ? overrides.partitionSet!
        : buildPartitionSet(),
    partitionSetName:
      overrides && overrides.hasOwnProperty('partitionSetName')
        ? overrides.partitionSetName!
        : 'quis',
    partitionStatusCounts:
      overrides && overrides.hasOwnProperty('partitionStatusCounts')
        ? overrides.partitionStatusCounts!
        : [
            buildPartitionStatusCounts(),
            buildPartitionStatusCounts(),
            buildPartitionStatusCounts(),
          ],
    partitionStatuses:
      overrides && overrides.hasOwnProperty('partitionStatuses')
        ? overrides.partitionStatuses!
        : buildPartitionStatuses(),
    reexecutionSteps:
      overrides && overrides.hasOwnProperty('reexecutionSteps')
        ? overrides.reexecutionSteps!
        : ['minus', 'quia', 'reprehenderit'],
    runs:
      overrides && overrides.hasOwnProperty('runs')
        ? overrides.runs!
        : [buildRun(), buildRun(), buildRun()],
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.BulkActionStatus.Canceled,
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 8.28,
    unfinishedRuns:
      overrides && overrides.hasOwnProperty('unfinishedRuns')
        ? overrides.unfinishedRuns!
        : [buildRun(), buildRun(), buildRun()],
  };
};

export const buildPartitionBackfills = (
  overrides?: Partial<Types.PartitionBackfills>,
): {__typename: 'PartitionBackfills'} & Types.PartitionBackfills => {
  return {
    __typename: 'PartitionBackfills',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildPartitionBackfill(), buildPartitionBackfill(), buildPartitionBackfill()],
  };
};

export const buildPartitionDefinition = (
  overrides?: Partial<Types.PartitionDefinition>,
): {__typename: 'PartitionDefinition'} & Types.PartitionDefinition => {
  return {
    __typename: 'PartitionDefinition',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'ab',
    dimensionTypes:
      overrides && overrides.hasOwnProperty('dimensionTypes')
        ? overrides.dimensionTypes!
        : [
            buildDimensionDefinitionType(),
            buildDimensionDefinitionType(),
            buildDimensionDefinitionType(),
          ],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'facilis',
    timeWindowMetadata:
      overrides && overrides.hasOwnProperty('timeWindowMetadata')
        ? overrides.timeWindowMetadata!
        : buildTimePartitionsDefinitionMetadata(),
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : Types.PartitionDefinitionType.Dynamic,
  };
};

export const buildPartitionRun = (
  overrides?: Partial<Types.PartitionRun>,
): {__typename: 'PartitionRun'} & Types.PartitionRun => {
  return {
    __typename: 'PartitionRun',
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'ut',
    partitionName:
      overrides && overrides.hasOwnProperty('partitionName') ? overrides.partitionName! : 'enim',
    run: overrides && overrides.hasOwnProperty('run') ? overrides.run! : buildRun(),
  };
};

export const buildPartitionRunConfig = (
  overrides?: Partial<Types.PartitionRunConfig>,
): {__typename: 'PartitionRunConfig'} & Types.PartitionRunConfig => {
  return {
    __typename: 'PartitionRunConfig',
    yaml: overrides && overrides.hasOwnProperty('yaml') ? overrides.yaml! : 'ab',
  };
};

export const buildPartitionSet = (
  overrides?: Partial<Types.PartitionSet>,
): {__typename: 'PartitionSet'} & Types.PartitionSet => {
  return {
    __typename: 'PartitionSet',
    backfills:
      overrides && overrides.hasOwnProperty('backfills')
        ? overrides.backfills!
        : [buildPartitionBackfill(), buildPartitionBackfill(), buildPartitionBackfill()],
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'e0ac1103-209e-4984-89c5-ba61a9d9b9f1',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'cupiditate',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'placeat',
    partition:
      overrides && overrides.hasOwnProperty('partition') ? overrides.partition! : buildPartition(),
    partitionRuns:
      overrides && overrides.hasOwnProperty('partitionRuns')
        ? overrides.partitionRuns!
        : [buildPartitionRun(), buildPartitionRun(), buildPartitionRun()],
    partitionStatusesOrError:
      overrides && overrides.hasOwnProperty('partitionStatusesOrError')
        ? overrides.partitionStatusesOrError!
        : buildPartitionStatuses(),
    partitionsOrError:
      overrides && overrides.hasOwnProperty('partitionsOrError')
        ? overrides.partitionsOrError!
        : buildPartitions(),
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'nihil',
    repositoryOrigin:
      overrides && overrides.hasOwnProperty('repositoryOrigin')
        ? overrides.repositoryOrigin!
        : buildRepositoryOrigin(),
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['voluptate', 'temporibus', 'eos'],
  };
};

export const buildPartitionSetNotFoundError = (
  overrides?: Partial<Types.PartitionSetNotFoundError>,
): {__typename: 'PartitionSetNotFoundError'} & Types.PartitionSetNotFoundError => {
  return {
    __typename: 'PartitionSetNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'corrupti',
    partitionSetName:
      overrides && overrides.hasOwnProperty('partitionSetName')
        ? overrides.partitionSetName!
        : 'rem',
  };
};

export const buildPartitionSetSelector = (
  overrides?: Partial<Types.PartitionSetSelector>,
): Types.PartitionSetSelector => {
  return {
    partitionSetName:
      overrides && overrides.hasOwnProperty('partitionSetName')
        ? overrides.partitionSetName!
        : 'soluta',
    repositorySelector:
      overrides && overrides.hasOwnProperty('repositorySelector')
        ? overrides.repositorySelector!
        : buildRepositorySelector(),
  };
};

export const buildPartitionSets = (
  overrides?: Partial<Types.PartitionSets>,
): {__typename: 'PartitionSets'} & Types.PartitionSets => {
  return {
    __typename: 'PartitionSets',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildPartitionSet(), buildPartitionSet(), buildPartitionSet()],
  };
};

export const buildPartitionStats = (
  overrides?: Partial<Types.PartitionStats>,
): {__typename: 'PartitionStats'} & Types.PartitionStats => {
  return {
    __typename: 'PartitionStats',
    numFailed: overrides && overrides.hasOwnProperty('numFailed') ? overrides.numFailed! : 4790,
    numMaterialized:
      overrides && overrides.hasOwnProperty('numMaterialized') ? overrides.numMaterialized! : 9478,
    numPartitions:
      overrides && overrides.hasOwnProperty('numPartitions') ? overrides.numPartitions! : 4096,
  };
};

export const buildPartitionStatus = (
  overrides?: Partial<Types.PartitionStatus>,
): {__typename: 'PartitionStatus'} & Types.PartitionStatus => {
  return {
    __typename: 'PartitionStatus',
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'ut',
    partitionName:
      overrides && overrides.hasOwnProperty('partitionName')
        ? overrides.partitionName!
        : 'voluptatem',
    runDuration:
      overrides && overrides.hasOwnProperty('runDuration') ? overrides.runDuration! : 2.33,
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'iusto',
    runStatus:
      overrides && overrides.hasOwnProperty('runStatus')
        ? overrides.runStatus!
        : Types.RunStatus.Canceled,
  };
};

export const buildPartitionStatusCounts = (
  overrides?: Partial<Types.PartitionStatusCounts>,
): {__typename: 'PartitionStatusCounts'} & Types.PartitionStatusCounts => {
  return {
    __typename: 'PartitionStatusCounts',
    count: overrides && overrides.hasOwnProperty('count') ? overrides.count! : 5809,
    runStatus:
      overrides && overrides.hasOwnProperty('runStatus')
        ? overrides.runStatus!
        : Types.RunStatus.Canceled,
  };
};

export const buildPartitionStatuses = (
  overrides?: Partial<Types.PartitionStatuses>,
): {__typename: 'PartitionStatuses'} & Types.PartitionStatuses => {
  return {
    __typename: 'PartitionStatuses',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildPartitionStatus(), buildPartitionStatus(), buildPartitionStatus()],
  };
};

export const buildPartitionTags = (
  overrides?: Partial<Types.PartitionTags>,
): {__typename: 'PartitionTags'} & Types.PartitionTags => {
  return {
    __typename: 'PartitionTags',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildPipelineTag(), buildPipelineTag(), buildPipelineTag()],
  };
};

export const buildPartitions = (
  overrides?: Partial<Types.Partitions>,
): {__typename: 'Partitions'} & Types.Partitions => {
  return {
    __typename: 'Partitions',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildPartition(), buildPartition(), buildPartition()],
  };
};

export const buildPathMetadataEntry = (
  overrides?: Partial<Types.PathMetadataEntry>,
): {__typename: 'PathMetadataEntry'} & Types.PathMetadataEntry => {
  return {
    __typename: 'PathMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'et',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'rerum',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : 'soluta',
  };
};

export const buildPermission = (
  overrides?: Partial<Types.Permission>,
): {__typename: 'Permission'} & Types.Permission => {
  return {
    __typename: 'Permission',
    disabledReason:
      overrides && overrides.hasOwnProperty('disabledReason') ? overrides.disabledReason! : 'dicta',
    permission:
      overrides && overrides.hasOwnProperty('permission') ? overrides.permission! : 'doloremque',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : true,
  };
};

export const buildPipeline = (
  overrides?: Partial<Types.Pipeline>,
): {__typename: 'Pipeline'} & Types.Pipeline => {
  return {
    __typename: 'Pipeline',
    dagsterTypeOrError:
      overrides && overrides.hasOwnProperty('dagsterTypeOrError')
        ? overrides.dagsterTypeOrError!
        : buildDagsterTypeNotFoundError(),
    dagsterTypes:
      overrides && overrides.hasOwnProperty('dagsterTypes')
        ? overrides.dagsterTypes!
        : [buildDagsterType(), buildDagsterType(), buildDagsterType()],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quisquam',
    graphName: overrides && overrides.hasOwnProperty('graphName') ? overrides.graphName! : 'eius',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'fda68e2a-475a-433c-8539-8a9b6fe6ccd5',
    isAssetJob: overrides && overrides.hasOwnProperty('isAssetJob') ? overrides.isAssetJob! : true,
    isJob: overrides && overrides.hasOwnProperty('isJob') ? overrides.isJob! : true,
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    modes:
      overrides && overrides.hasOwnProperty('modes')
        ? overrides.modes!
        : [buildMode(), buildMode(), buildMode()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'veritatis',
    parentSnapshotId:
      overrides && overrides.hasOwnProperty('parentSnapshotId')
        ? overrides.parentSnapshotId!
        : 'et',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'aperiam',
    presets:
      overrides && overrides.hasOwnProperty('presets')
        ? overrides.presets!
        : [buildPipelinePreset(), buildPipelinePreset(), buildPipelinePreset()],
    repository:
      overrides && overrides.hasOwnProperty('repository')
        ? overrides.repository!
        : buildRepository(),
    runs:
      overrides && overrides.hasOwnProperty('runs')
        ? overrides.runs!
        : [buildRun(), buildRun(), buildRun()],
    schedules:
      overrides && overrides.hasOwnProperty('schedules')
        ? overrides.schedules!
        : [buildSchedule(), buildSchedule(), buildSchedule()],
    sensors:
      overrides && overrides.hasOwnProperty('sensors')
        ? overrides.sensors!
        : [buildSensor(), buildSensor(), buildSensor()],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : buildSolidHandle(),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles')
        ? overrides.solidHandles!
        : [buildSolidHandle(), buildSolidHandle(), buildSolidHandle()],
    solids:
      overrides && overrides.hasOwnProperty('solids')
        ? overrides.solids!
        : [buildSolid(), buildSolid(), buildSolid()],
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildPipelineTag(), buildPipelineTag(), buildPipelineTag()],
  };
};

export const buildPipelineConfigValidationError = (
  overrides?: Partial<Types.PipelineConfigValidationError>,
): {__typename: 'PipelineConfigValidationError'} & Types.PipelineConfigValidationError => {
  return {
    __typename: 'PipelineConfigValidationError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'consequatur',
    path:
      overrides && overrides.hasOwnProperty('path')
        ? overrides.path!
        : ['temporibus', 'iusto', 'et'],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : Types.EvaluationErrorReason.FieldsNotDefined,
    stack:
      overrides && overrides.hasOwnProperty('stack') ? overrides.stack! : buildEvaluationStack(),
  };
};

export const buildPipelineConfigValidationInvalid = (
  overrides?: Partial<Types.PipelineConfigValidationInvalid>,
): {__typename: 'PipelineConfigValidationInvalid'} & Types.PipelineConfigValidationInvalid => {
  return {
    __typename: 'PipelineConfigValidationInvalid',
    errors:
      overrides && overrides.hasOwnProperty('errors')
        ? overrides.errors!
        : [
            buildPipelineConfigValidationError(),
            buildPipelineConfigValidationError(),
            buildPipelineConfigValidationError(),
          ],
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'totam',
  };
};

export const buildPipelineConfigValidationValid = (
  overrides?: Partial<Types.PipelineConfigValidationValid>,
): {__typename: 'PipelineConfigValidationValid'} & Types.PipelineConfigValidationValid => {
  return {
    __typename: 'PipelineConfigValidationValid',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'veniam',
  };
};

export const buildPipelineNotFoundError = (
  overrides?: Partial<Types.PipelineNotFoundError>,
): {__typename: 'PipelineNotFoundError'} & Types.PipelineNotFoundError => {
  return {
    __typename: 'PipelineNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'expedita',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'commodi',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'ducimus',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName')
        ? overrides.repositoryName!
        : 'possimus',
  };
};

export const buildPipelinePreset = (
  overrides?: Partial<Types.PipelinePreset>,
): {__typename: 'PipelinePreset'} & Types.PipelinePreset => {
  return {
    __typename: 'PipelinePreset',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'aperiam',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'saepe',
    runConfigYaml:
      overrides && overrides.hasOwnProperty('runConfigYaml') ? overrides.runConfigYaml! : 'et',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['reprehenderit', 'consequatur', 'sunt'],
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildPipelineTag(), buildPipelineTag(), buildPipelineTag()],
  };
};

export const buildPipelineReference = (
  overrides?: Partial<Types.PipelineReference>,
): {__typename: 'PipelineReference'} & Types.PipelineReference => {
  return {
    __typename: 'PipelineReference',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'iure',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['velit', 'et', 'sequi'],
  };
};

export const buildPipelineRun = (
  overrides?: Partial<Types.PipelineRun>,
): {__typename: 'PipelineRun'} & Types.PipelineRun => {
  return {
    __typename: 'PipelineRun',
    assets:
      overrides && overrides.hasOwnProperty('assets')
        ? overrides.assets!
        : [buildAsset(), buildAsset(), buildAsset()],
    canTerminate:
      overrides && overrides.hasOwnProperty('canTerminate') ? overrides.canTerminate! : false,
    capturedLogs:
      overrides && overrides.hasOwnProperty('capturedLogs')
        ? overrides.capturedLogs!
        : buildCapturedLogs(),
    computeLogs:
      overrides && overrides.hasOwnProperty('computeLogs')
        ? overrides.computeLogs!
        : buildComputeLogs(),
    eventConnection:
      overrides && overrides.hasOwnProperty('eventConnection')
        ? overrides.eventConnection!
        : buildEventConnection(),
    executionPlan:
      overrides && overrides.hasOwnProperty('executionPlan')
        ? overrides.executionPlan!
        : buildExecutionPlan(),
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'e58d70a8-15b2-44ab-ae86-04d9db6cd11f',
    jobName: overrides && overrides.hasOwnProperty('jobName') ? overrides.jobName! : 'consequatur',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'error',
    parentRunId:
      overrides && overrides.hasOwnProperty('parentRunId') ? overrides.parentRunId! : 'omnis',
    pipeline:
      overrides && overrides.hasOwnProperty('pipeline')
        ? overrides.pipeline!
        : buildPipelineReference(),
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'animi',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'fugiat',
    repositoryOrigin:
      overrides && overrides.hasOwnProperty('repositoryOrigin')
        ? overrides.repositoryOrigin!
        : buildRepositoryOrigin(),
    rootRunId: overrides && overrides.hasOwnProperty('rootRunId') ? overrides.rootRunId! : 'quia',
    runConfig:
      overrides && overrides.hasOwnProperty('runConfig') ? overrides.runConfig! : 'aspernatur',
    runConfigYaml:
      overrides && overrides.hasOwnProperty('runConfigYaml') ? overrides.runConfigYaml! : 'facere',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'tenetur',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['occaecati', 'assumenda', 'neque'],
    stats: overrides && overrides.hasOwnProperty('stats') ? overrides.stats! : buildPythonError(),
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.RunStatus.Canceled,
    stepKeysToExecute:
      overrides && overrides.hasOwnProperty('stepKeysToExecute')
        ? overrides.stepKeysToExecute!
        : ['qui', 'ea', 'et'],
    stepStats:
      overrides && overrides.hasOwnProperty('stepStats')
        ? overrides.stepStats!
        : [buildRunStepStats(), buildRunStepStats(), buildRunStepStats()],
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildPipelineTag(), buildPipelineTag(), buildPipelineTag()],
  };
};

export const buildPipelineRunConflict = (
  overrides?: Partial<Types.PipelineRunConflict>,
): {__typename: 'PipelineRunConflict'} & Types.PipelineRunConflict => {
  return {
    __typename: 'PipelineRunConflict',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'in',
  };
};

export const buildPipelineRunLogsSubscriptionFailure = (
  overrides?: Partial<Types.PipelineRunLogsSubscriptionFailure>,
): {
  __typename: 'PipelineRunLogsSubscriptionFailure';
} & Types.PipelineRunLogsSubscriptionFailure => {
  return {
    __typename: 'PipelineRunLogsSubscriptionFailure',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'vitae',
    missingRunId:
      overrides && overrides.hasOwnProperty('missingRunId') ? overrides.missingRunId! : 'cumque',
  };
};

export const buildPipelineRunLogsSubscriptionSuccess = (
  overrides?: Partial<Types.PipelineRunLogsSubscriptionSuccess>,
): {
  __typename: 'PipelineRunLogsSubscriptionSuccess';
} & Types.PipelineRunLogsSubscriptionSuccess => {
  return {
    __typename: 'PipelineRunLogsSubscriptionSuccess',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'id',
    hasMorePastEvents:
      overrides && overrides.hasOwnProperty('hasMorePastEvents')
        ? overrides.hasMorePastEvents!
        : true,
    messages:
      overrides && overrides.hasOwnProperty('messages')
        ? overrides.messages!
        : [buildAlertFailureEvent(), buildAlertFailureEvent(), buildAlertFailureEvent()],
    run: overrides && overrides.hasOwnProperty('run') ? overrides.run! : buildRun(),
  };
};

export const buildPipelineRunMetadataEntry = (
  overrides?: Partial<Types.PipelineRunMetadataEntry>,
): {__typename: 'PipelineRunMetadataEntry'} & Types.PipelineRunMetadataEntry => {
  return {
    __typename: 'PipelineRunMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'adipisci',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'soluta',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'dolorem',
  };
};

export const buildPipelineRunNotFoundError = (
  overrides?: Partial<Types.PipelineRunNotFoundError>,
): {__typename: 'PipelineRunNotFoundError'} & Types.PipelineRunNotFoundError => {
  return {
    __typename: 'PipelineRunNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'minus',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'rerum',
  };
};

export const buildPipelineRunStatsSnapshot = (
  overrides?: Partial<Types.PipelineRunStatsSnapshot>,
): {__typename: 'PipelineRunStatsSnapshot'} & Types.PipelineRunStatsSnapshot => {
  return {
    __typename: 'PipelineRunStatsSnapshot',
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 8.08,
    enqueuedTime:
      overrides && overrides.hasOwnProperty('enqueuedTime') ? overrides.enqueuedTime! : 9.65,
    expectations:
      overrides && overrides.hasOwnProperty('expectations') ? overrides.expectations! : 7156,
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'at',
    launchTime: overrides && overrides.hasOwnProperty('launchTime') ? overrides.launchTime! : 0.49,
    materializations:
      overrides && overrides.hasOwnProperty('materializations')
        ? overrides.materializations!
        : 8186,
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'cupiditate',
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 3.44,
    stepsFailed:
      overrides && overrides.hasOwnProperty('stepsFailed') ? overrides.stepsFailed! : 3219,
    stepsSucceeded:
      overrides && overrides.hasOwnProperty('stepsSucceeded') ? overrides.stepsSucceeded! : 3156,
  };
};

export const buildPipelineRunStepStats = (
  overrides?: Partial<Types.PipelineRunStepStats>,
): {__typename: 'PipelineRunStepStats'} & Types.PipelineRunStepStats => {
  return {
    __typename: 'PipelineRunStepStats',
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 3.31,
    expectationResults:
      overrides && overrides.hasOwnProperty('expectationResults')
        ? overrides.expectationResults!
        : [buildExpectationResult(), buildExpectationResult(), buildExpectationResult()],
    materializations:
      overrides && overrides.hasOwnProperty('materializations')
        ? overrides.materializations!
        : [buildMaterializationEvent(), buildMaterializationEvent(), buildMaterializationEvent()],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'et',
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 8.43,
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.StepEventStatus.Failure,
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'reiciendis',
  };
};

export const buildPipelineRuns = (
  overrides?: Partial<Types.PipelineRuns>,
): {__typename: 'PipelineRuns'} & Types.PipelineRuns => {
  return {
    __typename: 'PipelineRuns',
    count: overrides && overrides.hasOwnProperty('count') ? overrides.count! : 1847,
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildRun(), buildRun(), buildRun()],
  };
};

export const buildPipelineSelector = (
  overrides?: Partial<Types.PipelineSelector>,
): Types.PipelineSelector => {
  return {
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection')
        ? overrides.assetSelection!
        : [buildAssetKeyInput(), buildAssetKeyInput(), buildAssetKeyInput()],
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'commodi',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'quos',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName')
        ? overrides.repositoryName!
        : 'magnam',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['sunt', 'similique', 'sint'],
  };
};

export const buildPipelineSnapshot = (
  overrides?: Partial<Types.PipelineSnapshot>,
): {__typename: 'PipelineSnapshot'} & Types.PipelineSnapshot => {
  return {
    __typename: 'PipelineSnapshot',
    dagsterTypeOrError:
      overrides && overrides.hasOwnProperty('dagsterTypeOrError')
        ? overrides.dagsterTypeOrError!
        : buildDagsterTypeNotFoundError(),
    dagsterTypes:
      overrides && overrides.hasOwnProperty('dagsterTypes')
        ? overrides.dagsterTypes!
        : [buildDagsterType(), buildDagsterType(), buildDagsterType()],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'corporis',
    graphName:
      overrides && overrides.hasOwnProperty('graphName') ? overrides.graphName! : 'dolorum',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'a052bf7d-6918-434c-b95b-82d9dc5b3fb1',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    modes:
      overrides && overrides.hasOwnProperty('modes')
        ? overrides.modes!
        : [buildMode(), buildMode(), buildMode()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'beatae',
    parentSnapshotId:
      overrides && overrides.hasOwnProperty('parentSnapshotId')
        ? overrides.parentSnapshotId!
        : 'ut',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'labore',
    runs:
      overrides && overrides.hasOwnProperty('runs')
        ? overrides.runs!
        : [buildRun(), buildRun(), buildRun()],
    schedules:
      overrides && overrides.hasOwnProperty('schedules')
        ? overrides.schedules!
        : [buildSchedule(), buildSchedule(), buildSchedule()],
    sensors:
      overrides && overrides.hasOwnProperty('sensors')
        ? overrides.sensors!
        : [buildSensor(), buildSensor(), buildSensor()],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : buildSolidHandle(),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles')
        ? overrides.solidHandles!
        : [buildSolidHandle(), buildSolidHandle(), buildSolidHandle()],
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['quidem', 'ipsum', 'aspernatur'],
    solids:
      overrides && overrides.hasOwnProperty('solids')
        ? overrides.solids!
        : [buildSolid(), buildSolid(), buildSolid()],
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildPipelineTag(), buildPipelineTag(), buildPipelineTag()],
  };
};

export const buildPipelineSnapshotNotFoundError = (
  overrides?: Partial<Types.PipelineSnapshotNotFoundError>,
): {__typename: 'PipelineSnapshotNotFoundError'} & Types.PipelineSnapshotNotFoundError => {
  return {
    __typename: 'PipelineSnapshotNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'sit',
    snapshotId:
      overrides && overrides.hasOwnProperty('snapshotId') ? overrides.snapshotId! : 'quibusdam',
  };
};

export const buildPipelineTag = (
  overrides?: Partial<Types.PipelineTag>,
): {__typename: 'PipelineTag'} & Types.PipelineTag => {
  return {
    __typename: 'PipelineTag',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'qui',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'et',
  };
};

export const buildPipelineTagAndValues = (
  overrides?: Partial<Types.PipelineTagAndValues>,
): {__typename: 'PipelineTagAndValues'} & Types.PipelineTagAndValues => {
  return {
    __typename: 'PipelineTagAndValues',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'repudiandae',
    values:
      overrides && overrides.hasOwnProperty('values')
        ? overrides.values!
        : ['nesciunt', 'aliquid', 'fuga'],
  };
};

export const buildPresetNotFoundError = (
  overrides?: Partial<Types.PresetNotFoundError>,
): {__typename: 'PresetNotFoundError'} & Types.PresetNotFoundError => {
  return {
    __typename: 'PresetNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'provident',
    preset: overrides && overrides.hasOwnProperty('preset') ? overrides.preset! : 'necessitatibus',
  };
};

export const buildPythonArtifactMetadataEntry = (
  overrides?: Partial<Types.PythonArtifactMetadataEntry>,
): {__typename: 'PythonArtifactMetadataEntry'} & Types.PythonArtifactMetadataEntry => {
  return {
    __typename: 'PythonArtifactMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'ea',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'est',
    module: overrides && overrides.hasOwnProperty('module') ? overrides.module! : 'et',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'totam',
  };
};

export const buildPythonError = (
  overrides?: Partial<Types.PythonError>,
): {__typename: 'PythonError'} & Types.PythonError => {
  return {
    __typename: 'PythonError',
    cause: overrides && overrides.hasOwnProperty('cause') ? overrides.cause! : buildPythonError(),
    causes:
      overrides && overrides.hasOwnProperty('causes')
        ? overrides.causes!
        : [buildPythonError(), buildPythonError(), buildPythonError()],
    className: overrides && overrides.hasOwnProperty('className') ? overrides.className! : 'magni',
    errorChain:
      overrides && overrides.hasOwnProperty('errorChain')
        ? overrides.errorChain!
        : [buildErrorChainLink(), buildErrorChainLink(), buildErrorChainLink()],
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'veritatis',
    stack:
      overrides && overrides.hasOwnProperty('stack')
        ? overrides.stack!
        : ['modi', 'eos', 'recusandae'],
  };
};

export const buildReexecutionParams = (
  overrides?: Partial<Types.ReexecutionParams>,
): Types.ReexecutionParams => {
  return {
    parentRunId:
      overrides && overrides.hasOwnProperty('parentRunId') ? overrides.parentRunId! : 'sunt',
    strategy:
      overrides && overrides.hasOwnProperty('strategy')
        ? overrides.strategy!
        : Types.ReexecutionStrategy.AllSteps,
  };
};

export const buildRegularConfigType = (
  overrides?: Partial<Types.RegularConfigType>,
): {__typename: 'RegularConfigType'} & Types.RegularConfigType => {
  return {
    __typename: 'RegularConfigType',
    description:
      overrides && overrides.hasOwnProperty('description')
        ? overrides.description!
        : 'necessitatibus',
    givenName: overrides && overrides.hasOwnProperty('givenName') ? overrides.givenName! : 'saepe',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'quis',
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [buildConfigType(), buildConfigType(), buildConfigType()],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys')
        ? overrides.typeParamKeys!
        : ['quibusdam', 'architecto', 'suscipit'],
  };
};

export const buildRegularDagsterType = (
  overrides?: Partial<Types.RegularDagsterType>,
): {__typename: 'RegularDagsterType'} & Types.RegularDagsterType => {
  return {
    __typename: 'RegularDagsterType',
    description:
      overrides && overrides.hasOwnProperty('description')
        ? overrides.description!
        : 'necessitatibus',
    displayName:
      overrides && overrides.hasOwnProperty('displayName') ? overrides.displayName! : 'expedita',
    innerTypes:
      overrides && overrides.hasOwnProperty('innerTypes')
        ? overrides.innerTypes!
        : [buildDagsterType(), buildDagsterType(), buildDagsterType()],
    inputSchemaType:
      overrides && overrides.hasOwnProperty('inputSchemaType')
        ? overrides.inputSchemaType!
        : buildConfigType(),
    isBuiltin: overrides && overrides.hasOwnProperty('isBuiltin') ? overrides.isBuiltin! : true,
    isList: overrides && overrides.hasOwnProperty('isList') ? overrides.isList! : false,
    isNothing: overrides && overrides.hasOwnProperty('isNothing') ? overrides.isNothing! : false,
    isNullable: overrides && overrides.hasOwnProperty('isNullable') ? overrides.isNullable! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'maiores',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'velit',
    outputSchemaType:
      overrides && overrides.hasOwnProperty('outputSchemaType')
        ? overrides.outputSchemaType!
        : buildConfigType(),
  };
};

export const buildReloadNotSupported = (
  overrides?: Partial<Types.ReloadNotSupported>,
): {__typename: 'ReloadNotSupported'} & Types.ReloadNotSupported => {
  return {
    __typename: 'ReloadNotSupported',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'neque',
  };
};

export const buildReloadRepositoryLocationMutation = (
  overrides?: Partial<Types.ReloadRepositoryLocationMutation>,
): {__typename: 'ReloadRepositoryLocationMutation'} & Types.ReloadRepositoryLocationMutation => {
  return {
    __typename: 'ReloadRepositoryLocationMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output') ? overrides.Output! : buildPythonError(),
  };
};

export const buildReloadWorkspaceMutation = (
  overrides?: Partial<Types.ReloadWorkspaceMutation>,
): {__typename: 'ReloadWorkspaceMutation'} & Types.ReloadWorkspaceMutation => {
  return {
    __typename: 'ReloadWorkspaceMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output') ? overrides.Output! : buildPythonError(),
  };
};

export const buildRepository = (
  overrides?: Partial<Types.Repository>,
): {__typename: 'Repository'} & Types.Repository => {
  return {
    __typename: 'Repository',
    allTopLevelResourceDetails:
      overrides && overrides.hasOwnProperty('allTopLevelResourceDetails')
        ? overrides.allTopLevelResourceDetails!
        : [buildResourceDetails(), buildResourceDetails(), buildResourceDetails()],
    assetGroups:
      overrides && overrides.hasOwnProperty('assetGroups')
        ? overrides.assetGroups!
        : [buildAssetGroup(), buildAssetGroup(), buildAssetGroup()],
    assetNodes:
      overrides && overrides.hasOwnProperty('assetNodes')
        ? overrides.assetNodes!
        : [buildAssetNode(), buildAssetNode(), buildAssetNode()],
    displayMetadata:
      overrides && overrides.hasOwnProperty('displayMetadata')
        ? overrides.displayMetadata!
        : [buildRepositoryMetadata(), buildRepositoryMetadata(), buildRepositoryMetadata()],
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'e97f8841-e61d-451b-93f6-99aacfac2fad',
    jobs:
      overrides && overrides.hasOwnProperty('jobs')
        ? overrides.jobs!
        : [buildJob(), buildJob(), buildJob()],
    location:
      overrides && overrides.hasOwnProperty('location')
        ? overrides.location!
        : buildRepositoryLocation(),
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'dolor',
    origin:
      overrides && overrides.hasOwnProperty('origin') ? overrides.origin! : buildRepositoryOrigin(),
    partitionSets:
      overrides && overrides.hasOwnProperty('partitionSets')
        ? overrides.partitionSets!
        : [buildPartitionSet(), buildPartitionSet(), buildPartitionSet()],
    pipelines:
      overrides && overrides.hasOwnProperty('pipelines')
        ? overrides.pipelines!
        : [buildPipeline(), buildPipeline(), buildPipeline()],
    schedules:
      overrides && overrides.hasOwnProperty('schedules')
        ? overrides.schedules!
        : [buildSchedule(), buildSchedule(), buildSchedule()],
    sensors:
      overrides && overrides.hasOwnProperty('sensors')
        ? overrides.sensors!
        : [buildSensor(), buildSensor(), buildSensor()],
    usedSolid:
      overrides && overrides.hasOwnProperty('usedSolid') ? overrides.usedSolid! : buildUsedSolid(),
    usedSolids:
      overrides && overrides.hasOwnProperty('usedSolids')
        ? overrides.usedSolids!
        : [buildUsedSolid(), buildUsedSolid(), buildUsedSolid()],
  };
};

export const buildRepositoryConnection = (
  overrides?: Partial<Types.RepositoryConnection>,
): {__typename: 'RepositoryConnection'} & Types.RepositoryConnection => {
  return {
    __typename: 'RepositoryConnection',
    nodes:
      overrides && overrides.hasOwnProperty('nodes')
        ? overrides.nodes!
        : [buildRepository(), buildRepository(), buildRepository()],
  };
};

export const buildRepositoryLocation = (
  overrides?: Partial<Types.RepositoryLocation>,
): {__typename: 'RepositoryLocation'} & Types.RepositoryLocation => {
  return {
    __typename: 'RepositoryLocation',
    dagsterLibraryVersions:
      overrides && overrides.hasOwnProperty('dagsterLibraryVersions')
        ? overrides.dagsterLibraryVersions!
        : [
            buildDagsterLibraryVersion(),
            buildDagsterLibraryVersion(),
            buildDagsterLibraryVersion(),
          ],
    environmentPath:
      overrides && overrides.hasOwnProperty('environmentPath')
        ? overrides.environmentPath!
        : 'fugit',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'ef33cd04-a9ec-45e1-ac15-7b603ba55a14',
    isReloadSupported:
      overrides && overrides.hasOwnProperty('isReloadSupported')
        ? overrides.isReloadSupported!
        : false,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'ut',
    repositories:
      overrides && overrides.hasOwnProperty('repositories')
        ? overrides.repositories!
        : [buildRepository(), buildRepository(), buildRepository()],
    serverId: overrides && overrides.hasOwnProperty('serverId') ? overrides.serverId! : 'eum',
  };
};

export const buildRepositoryLocationNotFound = (
  overrides?: Partial<Types.RepositoryLocationNotFound>,
): {__typename: 'RepositoryLocationNotFound'} & Types.RepositoryLocationNotFound => {
  return {
    __typename: 'RepositoryLocationNotFound',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'sed',
  };
};

export const buildRepositoryMetadata = (
  overrides?: Partial<Types.RepositoryMetadata>,
): {__typename: 'RepositoryMetadata'} & Types.RepositoryMetadata => {
  return {
    __typename: 'RepositoryMetadata',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'reiciendis',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'deserunt',
  };
};

export const buildRepositoryNotFoundError = (
  overrides?: Partial<Types.RepositoryNotFoundError>,
): {__typename: 'RepositoryNotFoundError'} & Types.RepositoryNotFoundError => {
  return {
    __typename: 'RepositoryNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ut',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'ipsam',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'velit',
  };
};

export const buildRepositoryOrigin = (
  overrides?: Partial<Types.RepositoryOrigin>,
): {__typename: 'RepositoryOrigin'} & Types.RepositoryOrigin => {
  return {
    __typename: 'RepositoryOrigin',
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'magni',
    repositoryLocationMetadata:
      overrides && overrides.hasOwnProperty('repositoryLocationMetadata')
        ? overrides.repositoryLocationMetadata!
        : [buildRepositoryMetadata(), buildRepositoryMetadata(), buildRepositoryMetadata()],
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'dolores',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'magni',
  };
};

export const buildRepositorySelector = (
  overrides?: Partial<Types.RepositorySelector>,
): Types.RepositorySelector => {
  return {
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'facere',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'ipsam',
  };
};

export const buildResource = (
  overrides?: Partial<Types.Resource>,
): {__typename: 'Resource'} & Types.Resource => {
  return {
    __typename: 'Resource',
    configField:
      overrides && overrides.hasOwnProperty('configField')
        ? overrides.configField!
        : buildConfigTypeField(),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'perferendis',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'fuga',
  };
};

export const buildResourceDetails = (
  overrides?: Partial<Types.ResourceDetails>,
): {__typename: 'ResourceDetails'} & Types.ResourceDetails => {
  return {
    __typename: 'ResourceDetails',
    configFields:
      overrides && overrides.hasOwnProperty('configFields')
        ? overrides.configFields!
        : [buildConfigTypeField(), buildConfigTypeField(), buildConfigTypeField()],
    configuredValues:
      overrides && overrides.hasOwnProperty('configuredValues')
        ? overrides.configuredValues!
        : [buildConfiguredValue(), buildConfiguredValue(), buildConfiguredValue()],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'laudantium',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'praesentium',
  };
};

export const buildResourceDetailsList = (
  overrides?: Partial<Types.ResourceDetailsList>,
): {__typename: 'ResourceDetailsList'} & Types.ResourceDetailsList => {
  return {
    __typename: 'ResourceDetailsList',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildResourceDetails(), buildResourceDetails(), buildResourceDetails()],
  };
};

export const buildResourceInitFailureEvent = (
  overrides?: Partial<Types.ResourceInitFailureEvent>,
): {__typename: 'ResourceInitFailureEvent'} & Types.ResourceInitFailureEvent => {
  return {
    __typename: 'ResourceInitFailureEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quia',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'mollitia',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'hic',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'dolor',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'perferendis',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'minima',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'quidem',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'qui',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'fuga',
  };
};

export const buildResourceInitStartedEvent = (
  overrides?: Partial<Types.ResourceInitStartedEvent>,
): {__typename: 'ResourceInitStartedEvent'} & Types.ResourceInitStartedEvent => {
  return {
    __typename: 'ResourceInitStartedEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'et',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'incidunt',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    markerEnd:
      overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'numquam',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'odio',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'sapiente',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'magni',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'aut',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'similique',
  };
};

export const buildResourceInitSuccessEvent = (
  overrides?: Partial<Types.ResourceInitSuccessEvent>,
): {__typename: 'ResourceInitSuccessEvent'} & Types.ResourceInitSuccessEvent => {
  return {
    __typename: 'ResourceInitSuccessEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'qui',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'fugiat',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'fugiat',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'et',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ut',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'fuga',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'voluptatem',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'deserunt',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'voluptates',
  };
};

export const buildResourceNotFoundError = (
  overrides?: Partial<Types.ResourceNotFoundError>,
): {__typename: 'ResourceNotFoundError'} & Types.ResourceNotFoundError => {
  return {
    __typename: 'ResourceNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quo',
    resourceName:
      overrides && overrides.hasOwnProperty('resourceName') ? overrides.resourceName! : 'iure',
  };
};

export const buildResourceRequirement = (
  overrides?: Partial<Types.ResourceRequirement>,
): {__typename: 'ResourceRequirement'} & Types.ResourceRequirement => {
  return {
    __typename: 'ResourceRequirement',
    resourceKey:
      overrides && overrides.hasOwnProperty('resourceKey') ? overrides.resourceKey! : 'pariatur',
  };
};

export const buildResourceSelector = (
  overrides?: Partial<Types.ResourceSelector>,
): Types.ResourceSelector => {
  return {
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'autem',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'quasi',
    resourceName:
      overrides && overrides.hasOwnProperty('resourceName') ? overrides.resourceName! : 'animi',
  };
};

export const buildResumeBackfillSuccess = (
  overrides?: Partial<Types.ResumeBackfillSuccess>,
): {__typename: 'ResumeBackfillSuccess'} & Types.ResumeBackfillSuccess => {
  return {
    __typename: 'ResumeBackfillSuccess',
    backfillId:
      overrides && overrides.hasOwnProperty('backfillId') ? overrides.backfillId! : 'sint',
  };
};

export const buildRun = (overrides?: Partial<Types.Run>): {__typename: 'Run'} & Types.Run => {
  return {
    __typename: 'Run',
    assetMaterializations:
      overrides && overrides.hasOwnProperty('assetMaterializations')
        ? overrides.assetMaterializations!
        : [buildMaterializationEvent(), buildMaterializationEvent(), buildMaterializationEvent()],
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection')
        ? overrides.assetSelection!
        : [buildAssetKey(), buildAssetKey(), buildAssetKey()],
    assets:
      overrides && overrides.hasOwnProperty('assets')
        ? overrides.assets!
        : [buildAsset(), buildAsset(), buildAsset()],
    canTerminate:
      overrides && overrides.hasOwnProperty('canTerminate') ? overrides.canTerminate! : false,
    capturedLogs:
      overrides && overrides.hasOwnProperty('capturedLogs')
        ? overrides.capturedLogs!
        : buildCapturedLogs(),
    computeLogs:
      overrides && overrides.hasOwnProperty('computeLogs')
        ? overrides.computeLogs!
        : buildComputeLogs(),
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 7.08,
    eventConnection:
      overrides && overrides.hasOwnProperty('eventConnection')
        ? overrides.eventConnection!
        : buildEventConnection(),
    executionPlan:
      overrides && overrides.hasOwnProperty('executionPlan')
        ? overrides.executionPlan!
        : buildExecutionPlan(),
    hasDeletePermission:
      overrides && overrides.hasOwnProperty('hasDeletePermission')
        ? overrides.hasDeletePermission!
        : false,
    hasReExecutePermission:
      overrides && overrides.hasOwnProperty('hasReExecutePermission')
        ? overrides.hasReExecutePermission!
        : true,
    hasTerminatePermission:
      overrides && overrides.hasOwnProperty('hasTerminatePermission')
        ? overrides.hasTerminatePermission!
        : true,
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '1e257d13-8f67-444f-aeb2-b39ede89fbf5',
    jobName: overrides && overrides.hasOwnProperty('jobName') ? overrides.jobName! : 'ut',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'laboriosam',
    parentPipelineSnapshotId:
      overrides && overrides.hasOwnProperty('parentPipelineSnapshotId')
        ? overrides.parentPipelineSnapshotId!
        : 'est',
    parentRunId:
      overrides && overrides.hasOwnProperty('parentRunId') ? overrides.parentRunId! : 'modi',
    pipeline:
      overrides && overrides.hasOwnProperty('pipeline')
        ? overrides.pipeline!
        : buildPipelineReference(),
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'enim',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'optio',
    repositoryOrigin:
      overrides && overrides.hasOwnProperty('repositoryOrigin')
        ? overrides.repositoryOrigin!
        : buildRepositoryOrigin(),
    resolvedOpSelection:
      overrides && overrides.hasOwnProperty('resolvedOpSelection')
        ? overrides.resolvedOpSelection!
        : ['enim', 'assumenda', 'facilis'],
    rootRunId: overrides && overrides.hasOwnProperty('rootRunId') ? overrides.rootRunId! : 'fugit',
    runConfig: overrides && overrides.hasOwnProperty('runConfig') ? overrides.runConfig! : 'quas',
    runConfigYaml:
      overrides && overrides.hasOwnProperty('runConfigYaml') ? overrides.runConfigYaml! : 'eveniet',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'fuga',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['dolore', 'odio', 'consectetur'],
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 2.52,
    stats: overrides && overrides.hasOwnProperty('stats') ? overrides.stats! : buildPythonError(),
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.RunStatus.Canceled,
    stepKeysToExecute:
      overrides && overrides.hasOwnProperty('stepKeysToExecute')
        ? overrides.stepKeysToExecute!
        : ['enim', 'dolores', 'dolor'],
    stepStats:
      overrides && overrides.hasOwnProperty('stepStats')
        ? overrides.stepStats!
        : [buildRunStepStats(), buildRunStepStats(), buildRunStepStats()],
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildPipelineTag(), buildPipelineTag(), buildPipelineTag()],
    updateTime: overrides && overrides.hasOwnProperty('updateTime') ? overrides.updateTime! : 0,
  };
};

export const buildRunCanceledEvent = (
  overrides?: Partial<Types.RunCanceledEvent>,
): {__typename: 'RunCanceledEvent'} & Types.RunCanceledEvent => {
  return {
    __typename: 'RunCanceledEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'sed',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'aliquam',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'aperiam',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'porro',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'sapiente',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'libero',
  };
};

export const buildRunCancelingEvent = (
  overrides?: Partial<Types.RunCancelingEvent>,
): {__typename: 'RunCancelingEvent'} & Types.RunCancelingEvent => {
  return {
    __typename: 'RunCancelingEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'natus',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'ullam',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'minus',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'nisi',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'qui',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'tenetur',
  };
};

export const buildRunConfigSchema = (
  overrides?: Partial<Types.RunConfigSchema>,
): {__typename: 'RunConfigSchema'} & Types.RunConfigSchema => {
  return {
    __typename: 'RunConfigSchema',
    allConfigTypes:
      overrides && overrides.hasOwnProperty('allConfigTypes')
        ? overrides.allConfigTypes!
        : [buildConfigType(), buildConfigType(), buildConfigType()],
    isRunConfigValid:
      overrides && overrides.hasOwnProperty('isRunConfigValid')
        ? overrides.isRunConfigValid!
        : buildInvalidSubsetError(),
    rootConfigType:
      overrides && overrides.hasOwnProperty('rootConfigType')
        ? overrides.rootConfigType!
        : buildConfigType(),
  };
};

export const buildRunConfigValidationInvalid = (
  overrides?: Partial<Types.RunConfigValidationInvalid>,
): {__typename: 'RunConfigValidationInvalid'} & Types.RunConfigValidationInvalid => {
  return {
    __typename: 'RunConfigValidationInvalid',
    errors:
      overrides && overrides.hasOwnProperty('errors')
        ? overrides.errors!
        : [
            buildPipelineConfigValidationError(),
            buildPipelineConfigValidationError(),
            buildPipelineConfigValidationError(),
          ],
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'consequatur',
  };
};

export const buildRunConflict = (
  overrides?: Partial<Types.RunConflict>,
): {__typename: 'RunConflict'} & Types.RunConflict => {
  return {
    __typename: 'RunConflict',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'iste',
  };
};

export const buildRunDequeuedEvent = (
  overrides?: Partial<Types.RunDequeuedEvent>,
): {__typename: 'RunDequeuedEvent'} & Types.RunDequeuedEvent => {
  return {
    __typename: 'RunDequeuedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'laboriosam',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'quia',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'distinctio',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'autem',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'et',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'non',
  };
};

export const buildRunEnqueuedEvent = (
  overrides?: Partial<Types.RunEnqueuedEvent>,
): {__typename: 'RunEnqueuedEvent'} & Types.RunEnqueuedEvent => {
  return {
    __typename: 'RunEnqueuedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'saepe',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'alias',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'et',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'quis',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'quia',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'quae',
  };
};

export const buildRunEvent = (
  overrides?: Partial<Types.RunEvent>,
): {__typename: 'RunEvent'} & Types.RunEvent => {
  return {
    __typename: 'RunEvent',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'repudiandae',
  };
};

export const buildRunFailureEvent = (
  overrides?: Partial<Types.RunFailureEvent>,
): {__typename: 'RunFailureEvent'} & Types.RunFailureEvent => {
  return {
    __typename: 'RunFailureEvent',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'porro',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'voluptatem',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'eaque',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'molestiae',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'voluptas',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'at',
  };
};

export const buildRunGroup = (
  overrides?: Partial<Types.RunGroup>,
): {__typename: 'RunGroup'} & Types.RunGroup => {
  return {
    __typename: 'RunGroup',
    rootRunId: overrides && overrides.hasOwnProperty('rootRunId') ? overrides.rootRunId! : 'rem',
    runs:
      overrides && overrides.hasOwnProperty('runs')
        ? overrides.runs!
        : [buildRun(), buildRun(), buildRun()],
  };
};

export const buildRunGroupNotFoundError = (
  overrides?: Partial<Types.RunGroupNotFoundError>,
): {__typename: 'RunGroupNotFoundError'} & Types.RunGroupNotFoundError => {
  return {
    __typename: 'RunGroupNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quasi',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'natus',
  };
};

export const buildRunGroups = (
  overrides?: Partial<Types.RunGroups>,
): {__typename: 'RunGroups'} & Types.RunGroups => {
  return {
    __typename: 'RunGroups',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildRunGroup(), buildRunGroup(), buildRunGroup()],
  };
};

export const buildRunGroupsOrError = (
  overrides?: Partial<Types.RunGroupsOrError>,
): {__typename: 'RunGroupsOrError'} & Types.RunGroupsOrError => {
  return {
    __typename: 'RunGroupsOrError',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildRunGroup(), buildRunGroup(), buildRunGroup()],
  };
};

export const buildRunLauncher = (
  overrides?: Partial<Types.RunLauncher>,
): {__typename: 'RunLauncher'} & Types.RunLauncher => {
  return {
    __typename: 'RunLauncher',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'iure',
  };
};

export const buildRunMarker = (
  overrides?: Partial<Types.RunMarker>,
): {__typename: 'RunMarker'} & Types.RunMarker => {
  return {
    __typename: 'RunMarker',
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 5.55,
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 3.49,
  };
};

export const buildRunNotFoundError = (
  overrides?: Partial<Types.RunNotFoundError>,
): {__typename: 'RunNotFoundError'} & Types.RunNotFoundError => {
  return {
    __typename: 'RunNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'illo',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'non',
  };
};

export const buildRunRequest = (
  overrides?: Partial<Types.RunRequest>,
): {__typename: 'RunRequest'} & Types.RunRequest => {
  return {
    __typename: 'RunRequest',
    runConfigYaml:
      overrides && overrides.hasOwnProperty('runConfigYaml') ? overrides.runConfigYaml! : 'ut',
    runKey: overrides && overrides.hasOwnProperty('runKey') ? overrides.runKey! : 'eius',
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildPipelineTag(), buildPipelineTag(), buildPipelineTag()],
  };
};

export const buildRunStartEvent = (
  overrides?: Partial<Types.RunStartEvent>,
): {__typename: 'RunStartEvent'} & Types.RunStartEvent => {
  return {
    __typename: 'RunStartEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'est',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'praesentium',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'earum',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'blanditiis',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'dolorem',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'est',
  };
};

export const buildRunStartingEvent = (
  overrides?: Partial<Types.RunStartingEvent>,
): {__typename: 'RunStartingEvent'} & Types.RunStartingEvent => {
  return {
    __typename: 'RunStartingEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'commodi',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'dicta',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'omnis',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'nulla',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'recusandae',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'est',
  };
};

export const buildRunStatsSnapshot = (
  overrides?: Partial<Types.RunStatsSnapshot>,
): {__typename: 'RunStatsSnapshot'} & Types.RunStatsSnapshot => {
  return {
    __typename: 'RunStatsSnapshot',
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 5.18,
    enqueuedTime:
      overrides && overrides.hasOwnProperty('enqueuedTime') ? overrides.enqueuedTime! : 9.23,
    expectations:
      overrides && overrides.hasOwnProperty('expectations') ? overrides.expectations! : 5993,
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'et',
    launchTime: overrides && overrides.hasOwnProperty('launchTime') ? overrides.launchTime! : 8.17,
    materializations:
      overrides && overrides.hasOwnProperty('materializations')
        ? overrides.materializations!
        : 7077,
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'mollitia',
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 8.88,
    stepsFailed:
      overrides && overrides.hasOwnProperty('stepsFailed') ? overrides.stepsFailed! : 2566,
    stepsSucceeded:
      overrides && overrides.hasOwnProperty('stepsSucceeded') ? overrides.stepsSucceeded! : 1292,
  };
};

export const buildRunStepStats = (
  overrides?: Partial<Types.RunStepStats>,
): {__typename: 'RunStepStats'} & Types.RunStepStats => {
  return {
    __typename: 'RunStepStats',
    attempts:
      overrides && overrides.hasOwnProperty('attempts')
        ? overrides.attempts!
        : [buildRunMarker(), buildRunMarker(), buildRunMarker()],
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 0.92,
    expectationResults:
      overrides && overrides.hasOwnProperty('expectationResults')
        ? overrides.expectationResults!
        : [buildExpectationResult(), buildExpectationResult(), buildExpectationResult()],
    markers:
      overrides && overrides.hasOwnProperty('markers')
        ? overrides.markers!
        : [buildRunMarker(), buildRunMarker(), buildRunMarker()],
    materializations:
      overrides && overrides.hasOwnProperty('materializations')
        ? overrides.materializations!
        : [buildMaterializationEvent(), buildMaterializationEvent(), buildMaterializationEvent()],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'repudiandae',
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 7.96,
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.StepEventStatus.Failure,
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'at',
  };
};

export const buildRunSuccessEvent = (
  overrides?: Partial<Types.RunSuccessEvent>,
): {__typename: 'RunSuccessEvent'} & Types.RunSuccessEvent => {
  return {
    __typename: 'RunSuccessEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'dolor',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'ex',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'nulla',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'similique',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'aspernatur',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'optio',
  };
};

export const buildRunTagKeys = (
  overrides?: Partial<Types.RunTagKeys>,
): {__typename: 'RunTagKeys'} & Types.RunTagKeys => {
  return {
    __typename: 'RunTagKeys',
    keys:
      overrides && overrides.hasOwnProperty('keys')
        ? overrides.keys!
        : ['doloremque', 'veritatis', 'laboriosam'],
  };
};

export const buildRunTags = (
  overrides?: Partial<Types.RunTags>,
): {__typename: 'RunTags'} & Types.RunTags => {
  return {
    __typename: 'RunTags',
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildPipelineTagAndValues(), buildPipelineTagAndValues(), buildPipelineTagAndValues()],
  };
};

export const buildRuns = (overrides?: Partial<Types.Runs>): {__typename: 'Runs'} & Types.Runs => {
  return {
    __typename: 'Runs',
    count: overrides && overrides.hasOwnProperty('count') ? overrides.count! : 319,
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildRun(), buildRun(), buildRun()],
  };
};

export const buildRunsFilter = (overrides?: Partial<Types.RunsFilter>): Types.RunsFilter => {
  return {
    createdBefore:
      overrides && overrides.hasOwnProperty('createdBefore') ? overrides.createdBefore! : 2.25,
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'voluptatem',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'voluptas',
    runIds:
      overrides && overrides.hasOwnProperty('runIds')
        ? overrides.runIds!
        : ['hic', 'commodi', 'veniam'],
    snapshotId:
      overrides && overrides.hasOwnProperty('snapshotId') ? overrides.snapshotId! : 'quam',
    statuses:
      overrides && overrides.hasOwnProperty('statuses')
        ? overrides.statuses!
        : [Types.RunStatus.Canceled, Types.RunStatus.Canceled, Types.RunStatus.Canceled],
    tags:
      overrides && overrides.hasOwnProperty('tags')
        ? overrides.tags!
        : [buildExecutionTag(), buildExecutionTag(), buildExecutionTag()],
    updatedAfter:
      overrides && overrides.hasOwnProperty('updatedAfter') ? overrides.updatedAfter! : 6.85,
  };
};

export const buildRuntimeMismatchConfigError = (
  overrides?: Partial<Types.RuntimeMismatchConfigError>,
): {__typename: 'RuntimeMismatchConfigError'} & Types.RuntimeMismatchConfigError => {
  return {
    __typename: 'RuntimeMismatchConfigError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'molestiae',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : ['qui', 'et', 'ut'],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : Types.EvaluationErrorReason.FieldsNotDefined,
    stack:
      overrides && overrides.hasOwnProperty('stack') ? overrides.stack! : buildEvaluationStack(),
    valueRep: overrides && overrides.hasOwnProperty('valueRep') ? overrides.valueRep! : 'in',
  };
};

export const buildScalarUnionConfigType = (
  overrides?: Partial<Types.ScalarUnionConfigType>,
): {__typename: 'ScalarUnionConfigType'} & Types.ScalarUnionConfigType => {
  return {
    __typename: 'ScalarUnionConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'adipisci',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'quia',
    nonScalarType:
      overrides && overrides.hasOwnProperty('nonScalarType')
        ? overrides.nonScalarType!
        : buildConfigType(),
    nonScalarTypeKey:
      overrides && overrides.hasOwnProperty('nonScalarTypeKey')
        ? overrides.nonScalarTypeKey!
        : 'dolor',
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [buildConfigType(), buildConfigType(), buildConfigType()],
    scalarType:
      overrides && overrides.hasOwnProperty('scalarType')
        ? overrides.scalarType!
        : buildConfigType(),
    scalarTypeKey:
      overrides && overrides.hasOwnProperty('scalarTypeKey') ? overrides.scalarTypeKey! : 'esse',
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys')
        ? overrides.typeParamKeys!
        : ['porro', 'omnis', 'tempore'],
  };
};

export const buildSchedule = (
  overrides?: Partial<Types.Schedule>,
): {__typename: 'Schedule'} & Types.Schedule => {
  return {
    __typename: 'Schedule',
    cronSchedule:
      overrides && overrides.hasOwnProperty('cronSchedule') ? overrides.cronSchedule! : 'possimus',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'porro',
    executionTimezone:
      overrides && overrides.hasOwnProperty('executionTimezone')
        ? overrides.executionTimezone!
        : 'qui',
    futureTick:
      overrides && overrides.hasOwnProperty('futureTick')
        ? overrides.futureTick!
        : buildDryRunInstigationTick(),
    futureTicks:
      overrides && overrides.hasOwnProperty('futureTicks')
        ? overrides.futureTicks!
        : buildDryRunInstigationTicks(),
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '71db947a-c94a-4681-979f-7d72688947d9',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'in',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'ut',
    partitionSet:
      overrides && overrides.hasOwnProperty('partitionSet')
        ? overrides.partitionSet!
        : buildPartitionSet(),
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'voluptatem',
    potentialTickTimestamps:
      overrides && overrides.hasOwnProperty('potentialTickTimestamps')
        ? overrides.potentialTickTimestamps!
        : [7.42, 6.43, 2.06],
    scheduleState:
      overrides && overrides.hasOwnProperty('scheduleState')
        ? overrides.scheduleState!
        : buildInstigationState(),
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['aut', 'blanditiis', 'aut'],
  };
};

export const buildScheduleData = (
  overrides?: Partial<Types.ScheduleData>,
): {__typename: 'ScheduleData'} & Types.ScheduleData => {
  return {
    __typename: 'ScheduleData',
    cronSchedule:
      overrides && overrides.hasOwnProperty('cronSchedule') ? overrides.cronSchedule! : 'enim',
    startTimestamp:
      overrides && overrides.hasOwnProperty('startTimestamp') ? overrides.startTimestamp! : 9.43,
  };
};

export const buildScheduleNotFoundError = (
  overrides?: Partial<Types.ScheduleNotFoundError>,
): {__typename: 'ScheduleNotFoundError'} & Types.ScheduleNotFoundError => {
  return {
    __typename: 'ScheduleNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'velit',
    scheduleName:
      overrides && overrides.hasOwnProperty('scheduleName') ? overrides.scheduleName! : 'tempora',
  };
};

export const buildScheduleSelector = (
  overrides?: Partial<Types.ScheduleSelector>,
): Types.ScheduleSelector => {
  return {
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'nihil',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'illum',
    scheduleName:
      overrides && overrides.hasOwnProperty('scheduleName') ? overrides.scheduleName! : 'nisi',
  };
};

export const buildScheduleStateResult = (
  overrides?: Partial<Types.ScheduleStateResult>,
): {__typename: 'ScheduleStateResult'} & Types.ScheduleStateResult => {
  return {
    __typename: 'ScheduleStateResult',
    scheduleState:
      overrides && overrides.hasOwnProperty('scheduleState')
        ? overrides.scheduleState!
        : buildInstigationState(),
  };
};

export const buildScheduleTick = (
  overrides?: Partial<Types.ScheduleTick>,
): {__typename: 'ScheduleTick'} & Types.ScheduleTick => {
  return {
    __typename: 'ScheduleTick',
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.InstigationTickStatus.Failure,
    tickId: overrides && overrides.hasOwnProperty('tickId') ? overrides.tickId! : 'fugit',
    tickSpecificData:
      overrides && overrides.hasOwnProperty('tickSpecificData')
        ? overrides.tickSpecificData!
        : buildScheduleTickFailureData(),
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 2.14,
  };
};

export const buildScheduleTickFailureData = (
  overrides?: Partial<Types.ScheduleTickFailureData>,
): {__typename: 'ScheduleTickFailureData'} & Types.ScheduleTickFailureData => {
  return {
    __typename: 'ScheduleTickFailureData',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
  };
};

export const buildScheduleTickSuccessData = (
  overrides?: Partial<Types.ScheduleTickSuccessData>,
): {__typename: 'ScheduleTickSuccessData'} & Types.ScheduleTickSuccessData => {
  return {
    __typename: 'ScheduleTickSuccessData',
    run: overrides && overrides.hasOwnProperty('run') ? overrides.run! : buildRun(),
  };
};

export const buildScheduler = (
  overrides?: Partial<Types.Scheduler>,
): {__typename: 'Scheduler'} & Types.Scheduler => {
  return {
    __typename: 'Scheduler',
    schedulerClass:
      overrides && overrides.hasOwnProperty('schedulerClass') ? overrides.schedulerClass! : 'qui',
  };
};

export const buildSchedulerNotDefinedError = (
  overrides?: Partial<Types.SchedulerNotDefinedError>,
): {__typename: 'SchedulerNotDefinedError'} & Types.SchedulerNotDefinedError => {
  return {
    __typename: 'SchedulerNotDefinedError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quia',
  };
};

export const buildSchedules = (
  overrides?: Partial<Types.Schedules>,
): {__typename: 'Schedules'} & Types.Schedules => {
  return {
    __typename: 'Schedules',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildSchedule(), buildSchedule(), buildSchedule()],
  };
};

export const buildSelectorTypeConfigError = (
  overrides?: Partial<Types.SelectorTypeConfigError>,
): {__typename: 'SelectorTypeConfigError'} & Types.SelectorTypeConfigError => {
  return {
    __typename: 'SelectorTypeConfigError',
    incomingFields:
      overrides && overrides.hasOwnProperty('incomingFields')
        ? overrides.incomingFields!
        : ['ut', 'voluptas', 'alias'],
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'minima',
    path:
      overrides && overrides.hasOwnProperty('path') ? overrides.path! : ['et', 'modi', 'dolorem'],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : Types.EvaluationErrorReason.FieldsNotDefined,
    stack:
      overrides && overrides.hasOwnProperty('stack') ? overrides.stack! : buildEvaluationStack(),
  };
};

export const buildSensor = (
  overrides?: Partial<Types.Sensor>,
): {__typename: 'Sensor'} & Types.Sensor => {
  return {
    __typename: 'Sensor',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'sapiente',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '7ce6ea4d-e6d9-4e92-b8e8-4d5e3eacbcbd',
    jobOriginId:
      overrides && overrides.hasOwnProperty('jobOriginId') ? overrides.jobOriginId! : 'est',
    metadata:
      overrides && overrides.hasOwnProperty('metadata')
        ? overrides.metadata!
        : buildSensorMetadata(),
    minIntervalSeconds:
      overrides && overrides.hasOwnProperty('minIntervalSeconds')
        ? overrides.minIntervalSeconds!
        : 6078,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'quibusdam',
    nextTick:
      overrides && overrides.hasOwnProperty('nextTick')
        ? overrides.nextTick!
        : buildDryRunInstigationTick(),
    sensorState:
      overrides && overrides.hasOwnProperty('sensorState')
        ? overrides.sensorState!
        : buildInstigationState(),
    sensorType:
      overrides && overrides.hasOwnProperty('sensorType')
        ? overrides.sensorType!
        : Types.SensorType.Asset,
    targets:
      overrides && overrides.hasOwnProperty('targets')
        ? overrides.targets!
        : [buildTarget(), buildTarget(), buildTarget()],
  };
};

export const buildSensorData = (
  overrides?: Partial<Types.SensorData>,
): {__typename: 'SensorData'} & Types.SensorData => {
  return {
    __typename: 'SensorData',
    lastCursor:
      overrides && overrides.hasOwnProperty('lastCursor') ? overrides.lastCursor! : 'quae',
    lastRunKey:
      overrides && overrides.hasOwnProperty('lastRunKey') ? overrides.lastRunKey! : 'quas',
    lastTickTimestamp:
      overrides && overrides.hasOwnProperty('lastTickTimestamp')
        ? overrides.lastTickTimestamp!
        : 9.7,
  };
};

export const buildSensorMetadata = (
  overrides?: Partial<Types.SensorMetadata>,
): {__typename: 'SensorMetadata'} & Types.SensorMetadata => {
  return {
    __typename: 'SensorMetadata',
    assetKeys:
      overrides && overrides.hasOwnProperty('assetKeys')
        ? overrides.assetKeys!
        : [buildAssetKey(), buildAssetKey(), buildAssetKey()],
  };
};

export const buildSensorNotFoundError = (
  overrides?: Partial<Types.SensorNotFoundError>,
): {__typename: 'SensorNotFoundError'} & Types.SensorNotFoundError => {
  return {
    __typename: 'SensorNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'rerum',
    sensorName:
      overrides && overrides.hasOwnProperty('sensorName') ? overrides.sensorName! : 'corporis',
  };
};

export const buildSensorSelector = (
  overrides?: Partial<Types.SensorSelector>,
): Types.SensorSelector => {
  return {
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'enim',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName')
        ? overrides.repositoryName!
        : 'libero',
    sensorName:
      overrides && overrides.hasOwnProperty('sensorName') ? overrides.sensorName! : 'placeat',
  };
};

export const buildSensors = (
  overrides?: Partial<Types.Sensors>,
): {__typename: 'Sensors'} & Types.Sensors => {
  return {
    __typename: 'Sensors',
    results:
      overrides && overrides.hasOwnProperty('results')
        ? overrides.results!
        : [buildSensor(), buildSensor(), buildSensor()],
  };
};

export const buildSetSensorCursorMutation = (
  overrides?: Partial<Types.SetSensorCursorMutation>,
): {__typename: 'SetSensorCursorMutation'} & Types.SetSensorCursorMutation => {
  return {
    __typename: 'SetSensorCursorMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output') ? overrides.Output! : buildPythonError(),
  };
};

export const buildShutdownRepositoryLocationMutation = (
  overrides?: Partial<Types.ShutdownRepositoryLocationMutation>,
): {
  __typename: 'ShutdownRepositoryLocationMutation';
} & Types.ShutdownRepositoryLocationMutation => {
  return {
    __typename: 'ShutdownRepositoryLocationMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output') ? overrides.Output! : buildPythonError(),
  };
};

export const buildShutdownRepositoryLocationSuccess = (
  overrides?: Partial<Types.ShutdownRepositoryLocationSuccess>,
): {__typename: 'ShutdownRepositoryLocationSuccess'} & Types.ShutdownRepositoryLocationSuccess => {
  return {
    __typename: 'ShutdownRepositoryLocationSuccess',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'assumenda',
  };
};

export const buildSolid = (
  overrides?: Partial<Types.Solid>,
): {__typename: 'Solid'} & Types.Solid => {
  return {
    __typename: 'Solid',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : buildISolidDefinition(),
    inputs:
      overrides && overrides.hasOwnProperty('inputs')
        ? overrides.inputs!
        : [buildInput(), buildInput(), buildInput()],
    isDynamicMapped:
      overrides && overrides.hasOwnProperty('isDynamicMapped') ? overrides.isDynamicMapped! : true,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'rerum',
    outputs:
      overrides && overrides.hasOwnProperty('outputs')
        ? overrides.outputs!
        : [buildOutput(), buildOutput(), buildOutput()],
  };
};

export const buildSolidContainer = (
  overrides?: Partial<Types.SolidContainer>,
): {__typename: 'SolidContainer'} & Types.SolidContainer => {
  return {
    __typename: 'SolidContainer',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'velit',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'f00f8432-b561-43c1-8978-9fb5fd116ad3',
    modes:
      overrides && overrides.hasOwnProperty('modes')
        ? overrides.modes!
        : [buildMode(), buildMode(), buildMode()],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'nobis',
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : buildSolidHandle(),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles')
        ? overrides.solidHandles!
        : [buildSolidHandle(), buildSolidHandle(), buildSolidHandle()],
    solids:
      overrides && overrides.hasOwnProperty('solids')
        ? overrides.solids!
        : [buildSolid(), buildSolid(), buildSolid()],
  };
};

export const buildSolidDefinition = (
  overrides?: Partial<Types.SolidDefinition>,
): {__typename: 'SolidDefinition'} & Types.SolidDefinition => {
  return {
    __typename: 'SolidDefinition',
    assetNodes:
      overrides && overrides.hasOwnProperty('assetNodes')
        ? overrides.assetNodes!
        : [buildAssetNode(), buildAssetNode(), buildAssetNode()],
    configField:
      overrides && overrides.hasOwnProperty('configField')
        ? overrides.configField!
        : buildConfigTypeField(),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'qui',
    inputDefinitions:
      overrides && overrides.hasOwnProperty('inputDefinitions')
        ? overrides.inputDefinitions!
        : [buildInputDefinition(), buildInputDefinition(), buildInputDefinition()],
    metadata:
      overrides && overrides.hasOwnProperty('metadata')
        ? overrides.metadata!
        : [
            buildMetadataItemDefinition(),
            buildMetadataItemDefinition(),
            buildMetadataItemDefinition(),
          ],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'in',
    outputDefinitions:
      overrides && overrides.hasOwnProperty('outputDefinitions')
        ? overrides.outputDefinitions!
        : [buildOutputDefinition(), buildOutputDefinition(), buildOutputDefinition()],
    requiredResources:
      overrides && overrides.hasOwnProperty('requiredResources')
        ? overrides.requiredResources!
        : [buildResourceRequirement(), buildResourceRequirement(), buildResourceRequirement()],
  };
};

export const buildSolidHandle = (
  overrides?: Partial<Types.SolidHandle>,
): {__typename: 'SolidHandle'} & Types.SolidHandle => {
  return {
    __typename: 'SolidHandle',
    handleID: overrides && overrides.hasOwnProperty('handleID') ? overrides.handleID! : 'iusto',
    parent:
      overrides && overrides.hasOwnProperty('parent') ? overrides.parent! : buildSolidHandle(),
    solid: overrides && overrides.hasOwnProperty('solid') ? overrides.solid! : buildSolid(),
    stepStats:
      overrides && overrides.hasOwnProperty('stepStats')
        ? overrides.stepStats!
        : buildSolidStepStatsConnection(),
  };
};

export const buildSolidStepStatsConnection = (
  overrides?: Partial<Types.SolidStepStatsConnection>,
): {__typename: 'SolidStepStatsConnection'} & Types.SolidStepStatsConnection => {
  return {
    __typename: 'SolidStepStatsConnection',
    nodes:
      overrides && overrides.hasOwnProperty('nodes')
        ? overrides.nodes!
        : [buildRunStepStats(), buildRunStepStats(), buildRunStepStats()],
  };
};

export const buildSolidStepStatusUnavailableError = (
  overrides?: Partial<Types.SolidStepStatusUnavailableError>,
): {__typename: 'SolidStepStatusUnavailableError'} & Types.SolidStepStatusUnavailableError => {
  return {
    __typename: 'SolidStepStatusUnavailableError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'accusantium',
  };
};

export const buildStaleCause = (
  overrides?: Partial<Types.StaleCause>,
): {__typename: 'StaleCause'} & Types.StaleCause => {
  return {
    __typename: 'StaleCause',
    dependency:
      overrides && overrides.hasOwnProperty('dependency') ? overrides.dependency! : buildAssetKey(),
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : buildAssetKey(),
    reason: overrides && overrides.hasOwnProperty('reason') ? overrides.reason! : 'et',
  };
};

export const buildStartScheduleMutation = (
  overrides?: Partial<Types.StartScheduleMutation>,
): {__typename: 'StartScheduleMutation'} & Types.StartScheduleMutation => {
  return {
    __typename: 'StartScheduleMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output') ? overrides.Output! : buildPythonError(),
  };
};

export const buildStepEvent = (
  overrides?: Partial<Types.StepEvent>,
): {__typename: 'StepEvent'} & Types.StepEvent => {
  return {
    __typename: 'StepEvent',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'hic',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'labore',
  };
};

export const buildStepExecution = (
  overrides?: Partial<Types.StepExecution>,
): Types.StepExecution => {
  return {
    marshalledInputs:
      overrides && overrides.hasOwnProperty('marshalledInputs')
        ? overrides.marshalledInputs!
        : [buildMarshalledInput(), buildMarshalledInput(), buildMarshalledInput()],
    marshalledOutputs:
      overrides && overrides.hasOwnProperty('marshalledOutputs')
        ? overrides.marshalledOutputs!
        : [buildMarshalledOutput(), buildMarshalledOutput(), buildMarshalledOutput()],
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'nihil',
  };
};

export const buildStepExpectationResultEvent = (
  overrides?: Partial<Types.StepExpectationResultEvent>,
): {__typename: 'StepExpectationResultEvent'} & Types.StepExpectationResultEvent => {
  return {
    __typename: 'StepExpectationResultEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    expectationResult:
      overrides && overrides.hasOwnProperty('expectationResult')
        ? overrides.expectationResult!
        : buildExpectationResult(),
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ullam',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'nisi',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'voluptatem',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'praesentium',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'in',
  };
};

export const buildStepOutputHandle = (
  overrides?: Partial<Types.StepOutputHandle>,
): Types.StepOutputHandle => {
  return {
    outputName: overrides && overrides.hasOwnProperty('outputName') ? overrides.outputName! : 'non',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'et',
  };
};

export const buildStepWorkerStartedEvent = (
  overrides?: Partial<Types.StepWorkerStartedEvent>,
): {__typename: 'StepWorkerStartedEvent'} & Types.StepWorkerStartedEvent => {
  return {
    __typename: 'StepWorkerStartedEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'blanditiis',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'voluptatem',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'quod',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'quis',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'veritatis',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'nobis',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'placeat',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'minus',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'et',
  };
};

export const buildStepWorkerStartingEvent = (
  overrides?: Partial<Types.StepWorkerStartingEvent>,
): {__typename: 'StepWorkerStartingEvent'} & Types.StepWorkerStartingEvent => {
  return {
    __typename: 'StepWorkerStartingEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'sint',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : Types.DagsterEventType.AlertFailure,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'cupiditate',
    level:
      overrides && overrides.hasOwnProperty('level') ? overrides.level! : Types.LogLevel.Critical,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'qui',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'et',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'deserunt',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'adipisci',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'voluptatem',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'sunt',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'consequuntur',
  };
};

export const buildStopRunningScheduleMutation = (
  overrides?: Partial<Types.StopRunningScheduleMutation>,
): {__typename: 'StopRunningScheduleMutation'} & Types.StopRunningScheduleMutation => {
  return {
    __typename: 'StopRunningScheduleMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output') ? overrides.Output! : buildPythonError(),
  };
};

export const buildStopSensorMutation = (
  overrides?: Partial<Types.StopSensorMutation>,
): {__typename: 'StopSensorMutation'} & Types.StopSensorMutation => {
  return {
    __typename: 'StopSensorMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output') ? overrides.Output! : buildPythonError(),
  };
};

export const buildStopSensorMutationResult = (
  overrides?: Partial<Types.StopSensorMutationResult>,
): {__typename: 'StopSensorMutationResult'} & Types.StopSensorMutationResult => {
  return {
    __typename: 'StopSensorMutationResult',
    instigationState:
      overrides && overrides.hasOwnProperty('instigationState')
        ? overrides.instigationState!
        : buildInstigationState(),
  };
};

export const buildTable = (
  overrides?: Partial<Types.Table>,
): {__typename: 'Table'} & Types.Table => {
  return {
    __typename: 'Table',
    records:
      overrides && overrides.hasOwnProperty('records')
        ? overrides.records!
        : ['sed', 'autem', 'laudantium'],
    schema:
      overrides && overrides.hasOwnProperty('schema') ? overrides.schema! : buildTableSchema(),
  };
};

export const buildTableColumn = (
  overrides?: Partial<Types.TableColumn>,
): {__typename: 'TableColumn'} & Types.TableColumn => {
  return {
    __typename: 'TableColumn',
    constraints:
      overrides && overrides.hasOwnProperty('constraints')
        ? overrides.constraints!
        : buildTableColumnConstraints(),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'illum',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'explicabo',
    type: overrides && overrides.hasOwnProperty('type') ? overrides.type! : 'a',
  };
};

export const buildTableColumnConstraints = (
  overrides?: Partial<Types.TableColumnConstraints>,
): {__typename: 'TableColumnConstraints'} & Types.TableColumnConstraints => {
  return {
    __typename: 'TableColumnConstraints',
    nullable: overrides && overrides.hasOwnProperty('nullable') ? overrides.nullable! : true,
    other:
      overrides && overrides.hasOwnProperty('other')
        ? overrides.other!
        : ['quibusdam', 'consequatur', 'saepe'],
    unique: overrides && overrides.hasOwnProperty('unique') ? overrides.unique! : false,
  };
};

export const buildTableConstraints = (
  overrides?: Partial<Types.TableConstraints>,
): {__typename: 'TableConstraints'} & Types.TableConstraints => {
  return {
    __typename: 'TableConstraints',
    other:
      overrides && overrides.hasOwnProperty('other')
        ? overrides.other!
        : ['dolorum', 'unde', 'odio'],
  };
};

export const buildTableMetadataEntry = (
  overrides?: Partial<Types.TableMetadataEntry>,
): {__typename: 'TableMetadataEntry'} & Types.TableMetadataEntry => {
  return {
    __typename: 'TableMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'sed',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'quia',
    table: overrides && overrides.hasOwnProperty('table') ? overrides.table! : buildTable(),
  };
};

export const buildTableSchema = (
  overrides?: Partial<Types.TableSchema>,
): {__typename: 'TableSchema'} & Types.TableSchema => {
  return {
    __typename: 'TableSchema',
    columns:
      overrides && overrides.hasOwnProperty('columns')
        ? overrides.columns!
        : [buildTableColumn(), buildTableColumn(), buildTableColumn()],
    constraints:
      overrides && overrides.hasOwnProperty('constraints')
        ? overrides.constraints!
        : buildTableConstraints(),
  };
};

export const buildTableSchemaMetadataEntry = (
  overrides?: Partial<Types.TableSchemaMetadataEntry>,
): {__typename: 'TableSchemaMetadataEntry'} & Types.TableSchemaMetadataEntry => {
  return {
    __typename: 'TableSchemaMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'itaque',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'libero',
    schema:
      overrides && overrides.hasOwnProperty('schema') ? overrides.schema! : buildTableSchema(),
  };
};

export const buildTarget = (
  overrides?: Partial<Types.Target>,
): {__typename: 'Target'} & Types.Target => {
  return {
    __typename: 'Target',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'porro',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'aut',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['non', 'labore', 'accusamus'],
  };
};

export const buildTerminatePipelineExecutionFailure = (
  overrides?: Partial<Types.TerminatePipelineExecutionFailure>,
): {__typename: 'TerminatePipelineExecutionFailure'} & Types.TerminatePipelineExecutionFailure => {
  return {
    __typename: 'TerminatePipelineExecutionFailure',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'vero',
    run: overrides && overrides.hasOwnProperty('run') ? overrides.run! : buildRun(),
  };
};

export const buildTerminatePipelineExecutionSuccess = (
  overrides?: Partial<Types.TerminatePipelineExecutionSuccess>,
): {__typename: 'TerminatePipelineExecutionSuccess'} & Types.TerminatePipelineExecutionSuccess => {
  return {
    __typename: 'TerminatePipelineExecutionSuccess',
    run: overrides && overrides.hasOwnProperty('run') ? overrides.run! : buildRun(),
  };
};

export const buildTerminateRunFailure = (
  overrides?: Partial<Types.TerminateRunFailure>,
): {__typename: 'TerminateRunFailure'} & Types.TerminateRunFailure => {
  return {
    __typename: 'TerminateRunFailure',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'sit',
    run: overrides && overrides.hasOwnProperty('run') ? overrides.run! : buildRun(),
  };
};

export const buildTerminateRunMutation = (
  overrides?: Partial<Types.TerminateRunMutation>,
): {__typename: 'TerminateRunMutation'} & Types.TerminateRunMutation => {
  return {
    __typename: 'TerminateRunMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output') ? overrides.Output! : buildPythonError(),
  };
};

export const buildTerminateRunSuccess = (
  overrides?: Partial<Types.TerminateRunSuccess>,
): {__typename: 'TerminateRunSuccess'} & Types.TerminateRunSuccess => {
  return {
    __typename: 'TerminateRunSuccess',
    run: overrides && overrides.hasOwnProperty('run') ? overrides.run! : buildRun(),
  };
};

export const buildTestFields = (
  overrides?: Partial<Types.TestFields>,
): {__typename: 'TestFields'} & Types.TestFields => {
  return {
    __typename: 'TestFields',
    alwaysException:
      overrides && overrides.hasOwnProperty('alwaysException')
        ? overrides.alwaysException!
        : 'quibusdam',
  };
};

export const buildTextMetadataEntry = (
  overrides?: Partial<Types.TextMetadataEntry>,
): {__typename: 'TextMetadataEntry'} & Types.TextMetadataEntry => {
  return {
    __typename: 'TextMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'illum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'quae',
    text: overrides && overrides.hasOwnProperty('text') ? overrides.text! : 'dignissimos',
  };
};

export const buildTickEvaluation = (
  overrides?: Partial<Types.TickEvaluation>,
): {__typename: 'TickEvaluation'} & Types.TickEvaluation => {
  return {
    __typename: 'TickEvaluation',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'est',
    error: overrides && overrides.hasOwnProperty('error') ? overrides.error! : buildPythonError(),
    runRequests:
      overrides && overrides.hasOwnProperty('runRequests')
        ? overrides.runRequests!
        : [buildRunRequest(), buildRunRequest(), buildRunRequest()],
    skipReason:
      overrides && overrides.hasOwnProperty('skipReason') ? overrides.skipReason! : 'dicta',
  };
};

export const buildTimePartitionRange = (
  overrides?: Partial<Types.TimePartitionRange>,
): {__typename: 'TimePartitionRange'} & Types.TimePartitionRange => {
  return {
    __typename: 'TimePartitionRange',
    endKey: overrides && overrides.hasOwnProperty('endKey') ? overrides.endKey! : 'dolorum',
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 8.87,
    startKey: overrides && overrides.hasOwnProperty('startKey') ? overrides.startKey! : 'sint',
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 1.83,
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : Types.PartitionRangeStatus.Failed,
  };
};

export const buildTimePartitions = (
  overrides?: Partial<Types.TimePartitions>,
): {__typename: 'TimePartitions'} & Types.TimePartitions => {
  return {
    __typename: 'TimePartitions',
    ranges:
      overrides && overrides.hasOwnProperty('ranges')
        ? overrides.ranges!
        : [buildTimePartitionRange(), buildTimePartitionRange(), buildTimePartitionRange()],
  };
};

export const buildTimePartitionsDefinitionMetadata = (
  overrides?: Partial<Types.TimePartitionsDefinitionMetadata>,
): {__typename: 'TimePartitionsDefinitionMetadata'} & Types.TimePartitionsDefinitionMetadata => {
  return {
    __typename: 'TimePartitionsDefinitionMetadata',
    endKey: overrides && overrides.hasOwnProperty('endKey') ? overrides.endKey! : 'nobis',
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 4.51,
    startKey: overrides && overrides.hasOwnProperty('startKey') ? overrides.startKey! : 'atque',
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 3.29,
  };
};

export const buildTypeCheck = (
  overrides?: Partial<Types.TypeCheck>,
): {__typename: 'TypeCheck'} & Types.TypeCheck => {
  return {
    __typename: 'TypeCheck',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'odio',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'accusamus',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries')
        ? overrides.metadataEntries!
        : [buildMetadataEntry(), buildMetadataEntry(), buildMetadataEntry()],
    success: overrides && overrides.hasOwnProperty('success') ? overrides.success! : true,
  };
};

export const buildUnauthorizedError = (
  overrides?: Partial<Types.UnauthorizedError>,
): {__typename: 'UnauthorizedError'} & Types.UnauthorizedError => {
  return {
    __typename: 'UnauthorizedError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'porro',
  };
};

export const buildUnknownPipeline = (
  overrides?: Partial<Types.UnknownPipeline>,
): {__typename: 'UnknownPipeline'} & Types.UnknownPipeline => {
  return {
    __typename: 'UnknownPipeline',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'dicta',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection')
        ? overrides.solidSelection!
        : ['rerum', 'enim', 'maiores'],
  };
};

export const buildUrlMetadataEntry = (
  overrides?: Partial<Types.UrlMetadataEntry>,
): {__typename: 'UrlMetadataEntry'} & Types.UrlMetadataEntry => {
  return {
    __typename: 'UrlMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'cum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'ut',
    url: overrides && overrides.hasOwnProperty('url') ? overrides.url! : 'optio',
  };
};

export const buildUsedSolid = (
  overrides?: Partial<Types.UsedSolid>,
): {__typename: 'UsedSolid'} & Types.UsedSolid => {
  return {
    __typename: 'UsedSolid',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : buildISolidDefinition(),
    invocations:
      overrides && overrides.hasOwnProperty('invocations')
        ? overrides.invocations!
        : [buildNodeInvocationSite(), buildNodeInvocationSite(), buildNodeInvocationSite()],
  };
};

export const buildWorkspace = (
  overrides?: Partial<Types.Workspace>,
): {__typename: 'Workspace'} & Types.Workspace => {
  return {
    __typename: 'Workspace',
    locationEntries:
      overrides && overrides.hasOwnProperty('locationEntries')
        ? overrides.locationEntries!
        : [
            buildWorkspaceLocationEntry(),
            buildWorkspaceLocationEntry(),
            buildWorkspaceLocationEntry(),
          ],
  };
};

export const buildWorkspaceLocationEntry = (
  overrides?: Partial<Types.WorkspaceLocationEntry>,
): {__typename: 'WorkspaceLocationEntry'} & Types.WorkspaceLocationEntry => {
  return {
    __typename: 'WorkspaceLocationEntry',
    displayMetadata:
      overrides && overrides.hasOwnProperty('displayMetadata')
        ? overrides.displayMetadata!
        : [buildRepositoryMetadata(), buildRepositoryMetadata(), buildRepositoryMetadata()],
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '6b0adcaa-46a3-49a8-98bb-9f5288e9711a',
    loadStatus:
      overrides && overrides.hasOwnProperty('loadStatus')
        ? overrides.loadStatus!
        : Types.RepositoryLocationLoadStatus.Loaded,
    locationOrLoadError:
      overrides && overrides.hasOwnProperty('locationOrLoadError')
        ? overrides.locationOrLoadError!
        : buildPythonError(),
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'sint',
    permissions:
      overrides && overrides.hasOwnProperty('permissions')
        ? overrides.permissions!
        : [buildPermission(), buildPermission(), buildPermission()],
    updatedTimestamp:
      overrides && overrides.hasOwnProperty('updatedTimestamp')
        ? overrides.updatedTimestamp!
        : 2.68,
  };
};

export const buildWorkspaceLocationStatusEntries = (
  overrides?: Partial<Types.WorkspaceLocationStatusEntries>,
): {__typename: 'WorkspaceLocationStatusEntries'} & Types.WorkspaceLocationStatusEntries => {
  return {
    __typename: 'WorkspaceLocationStatusEntries',
    entries:
      overrides && overrides.hasOwnProperty('entries')
        ? overrides.entries!
        : [
            buildWorkspaceLocationStatusEntry(),
            buildWorkspaceLocationStatusEntry(),
            buildWorkspaceLocationStatusEntry(),
          ],
  };
};

export const buildWorkspaceLocationStatusEntry = (
  overrides?: Partial<Types.WorkspaceLocationStatusEntry>,
): {__typename: 'WorkspaceLocationStatusEntry'} & Types.WorkspaceLocationStatusEntry => {
  return {
    __typename: 'WorkspaceLocationStatusEntry',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '485aa087-be75-4f2b-a1bc-be732927a8cc',
    loadStatus:
      overrides && overrides.hasOwnProperty('loadStatus')
        ? overrides.loadStatus!
        : Types.RepositoryLocationLoadStatus.Loaded,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'corporis',
    updateTimestamp:
      overrides && overrides.hasOwnProperty('updateTimestamp') ? overrides.updateTimestamp! : 7.09,
  };
};

export const buildWrappingConfigType = (
  overrides?: Partial<Types.WrappingConfigType>,
): {__typename: 'WrappingConfigType'} & Types.WrappingConfigType => {
  return {
    __typename: 'WrappingConfigType',
    ofType: overrides && overrides.hasOwnProperty('ofType') ? overrides.ofType! : buildConfigType(),
  };
};

export const buildWrappingDagsterType = (
  overrides?: Partial<Types.WrappingDagsterType>,
): {__typename: 'WrappingDagsterType'} & Types.WrappingDagsterType => {
  return {
    __typename: 'WrappingDagsterType',
    ofType:
      overrides && overrides.hasOwnProperty('ofType') ? overrides.ofType! : buildDagsterType(),
  };
};
