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
  partitions?: InputMaybe<Array<Scalars['String']>>;
  tags?: InputMaybe<Array<InputTag>>;
};

export type AssetAssetObservationsArgs = {
  afterTimestampMillis?: InputMaybe<Scalars['String']>;
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitionInLast?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<Scalars['String']>>;
};

export type AssetBackfillData = {
  __typename: 'AssetBackfillData';
  assetBackfillStatuses: Array<AssetBackfillStatus>;
  rootAssetTargetedPartitions: Maybe<Array<Scalars['String']>>;
  rootAssetTargetedRanges: Maybe<Array<PartitionKeyRange>>;
};

export type AssetBackfillStatus = AssetPartitionsStatusCounts | UnpartitionedAssetStatus;

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
  autoMaterializePolicy: Maybe<AutoMaterializePolicy>;
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
  partitions?: InputMaybe<Array<Scalars['String']>>;
};

export type AssetNodeAssetObservationsArgs = {
  beforeTimestampMillis?: InputMaybe<Scalars['String']>;
  limit?: InputMaybe<Scalars['Int']>;
  partitions?: InputMaybe<Array<Scalars['String']>>;
};

export type AssetNodeLatestMaterializationByPartitionArgs = {
  partitions?: InputMaybe<Array<Scalars['String']>>;
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

export type AssetPartitionStatuses =
  | DefaultPartitionStatuses
  | MultiPartitionStatuses
  | TimePartitionStatuses;

export type AssetPartitionsStatusCounts = {
  __typename: 'AssetPartitionsStatusCounts';
  assetKey: AssetKey;
  numPartitionsFailed: Scalars['Int'];
  numPartitionsInProgress: Scalars['Int'];
  numPartitionsMaterialized: Scalars['Int'];
  numPartitionsTargeted: Scalars['Int'];
};

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

export type AutoMaterializeAssetEvaluationNeedsMigrationError = Error & {
  __typename: 'AutoMaterializeAssetEvaluationNeedsMigrationError';
  message: Scalars['String'];
};

export type AutoMaterializeAssetEvaluationRecord = {
  __typename: 'AutoMaterializeAssetEvaluationRecord';
  conditions: Array<AutoMaterializeCondition>;
  evaluationId: Scalars['Int'];
  id: Scalars['ID'];
  numDiscarded: Scalars['Int'];
  numRequested: Scalars['Int'];
  numSkipped: Scalars['Int'];
  runIds: Array<Scalars['String']>;
  timestamp: Scalars['Float'];
};

export type AutoMaterializeAssetEvaluationRecords = {
  __typename: 'AutoMaterializeAssetEvaluationRecords';
  currentEvaluationId: Maybe<Scalars['Int']>;
  records: Array<AutoMaterializeAssetEvaluationRecord>;
};

export type AutoMaterializeAssetEvaluationRecordsOrError =
  | AutoMaterializeAssetEvaluationNeedsMigrationError
  | AutoMaterializeAssetEvaluationRecords;

export type AutoMaterializeCondition =
  | DownstreamFreshnessAutoMaterializeCondition
  | FreshnessAutoMaterializeCondition
  | MaxMaterializationsExceededAutoMaterializeCondition
  | MissingAutoMaterializeCondition
  | ParentMaterializedAutoMaterializeCondition
  | ParentOutdatedAutoMaterializeCondition;

export type AutoMaterializeConditionWithDecisionType = {
  decisionType: AutoMaterializeDecisionType;
  partitionKeysOrError: Maybe<PartitionKeysOrError>;
};

export enum AutoMaterializeDecisionType {
  DISCARD = 'DISCARD',
  MATERIALIZE = 'MATERIALIZE',
  SKIP = 'SKIP',
}

export type AutoMaterializePolicy = {
  __typename: 'AutoMaterializePolicy';
  maxMaterializationsPerMinute: Maybe<Scalars['Int']>;
  policyType: AutoMaterializePolicyType;
};

export enum AutoMaterializePolicyType {
  EAGER = 'EAGER',
  LAZY = 'LAZY',
}

export type BackfillNotFoundError = Error & {
  __typename: 'BackfillNotFoundError';
  backfillId: Scalars['String'];
  message: Scalars['String'];
};

export type BoolMetadataEntry = MetadataEntry & {
  __typename: 'BoolMetadataEntry';
  boolValue: Maybe<Scalars['Boolean']>;
  description: Maybe<Scalars['String']>;
  label: Scalars['String'];
};

export enum BulkActionStatus {
  CANCELED = 'CANCELED',
  CANCELING = 'CANCELING',
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

export type ConcurrencyKeyInfo = {
  __typename: 'ConcurrencyKeyInfo';
  activeRunIds: Array<Scalars['String']>;
  activeSlotCount: Scalars['Int'];
  assignedStepCount: Scalars['Int'];
  assignedStepRunIds: Array<Scalars['String']>;
  concurrencyKey: Scalars['String'];
  pendingStepCount: Scalars['Int'];
  pendingStepRunIds: Array<Scalars['String']>;
  slotCount: Scalars['Int'];
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
  freeConcurrencySlotsForRun: Scalars['Boolean'];
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
  setAutoMaterializePaused: Scalars['Boolean'];
  setConcurrencyLimit: Scalars['Boolean'];
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

export type DagitMutationFreeConcurrencySlotsForRunArgs = {
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

export type DagitMutationSetAutoMaterializePausedArgs = {
  paused: Scalars['Boolean'];
};

export type DagitMutationSetConcurrencyLimitArgs = {
  concurrencyKey: Scalars['String'];
  limit: Scalars['Int'];
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
  autoMaterializeAssetEvaluationsOrError: Maybe<AutoMaterializeAssetEvaluationRecordsOrError>;
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

export type DagitQueryAutoMaterializeAssetEvaluationsOrErrorArgs = {
  assetKey: AssetKeyInput;
  cursor?: InputMaybe<Scalars['String']>;
  limit: Scalars['Int'];
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
  scheduleStatus?: InputMaybe<InstigationStatus>;
};

export type DagitQuerySensorOrErrorArgs = {
  sensorSelector: SensorSelector;
};

export type DagitQuerySensorsOrErrorArgs = {
  repositorySelector: RepositorySelector;
  sensorStatus?: InputMaybe<InstigationStatus>;
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

export type DefaultPartitionStatuses = {
  __typename: 'DefaultPartitionStatuses';
  failedPartitions: Array<Scalars['String']>;
  materializedPartitions: Array<Scalars['String']>;
  materializingPartitions: Array<Scalars['String']>;
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
  dynamicPartitionsDefinitionName: Maybe<Scalars['String']>;
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

export type DownstreamFreshnessAutoMaterializeCondition = AutoMaterializeConditionWithDecisionType & {
  __typename: 'DownstreamFreshnessAutoMaterializeCondition';
  decisionType: AutoMaterializeDecisionType;
  partitionKeysOrError: Maybe<PartitionKeysOrError>;
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

export type DynamicPartitionRequest = {
  __typename: 'DynamicPartitionRequest';
  partitionKeys: Maybe<Array<Scalars['String']>>;
  partitionsDefName: Scalars['String'];
  type: DynamicPartitionsRequestType;
};

export type DynamicPartitionsRequestResult = {
  __typename: 'DynamicPartitionsRequestResult';
  partitionKeys: Maybe<Array<Scalars['String']>>;
  partitionsDefName: Scalars['String'];
  skippedPartitionKeys: Array<Scalars['String']>;
  type: DynamicPartitionsRequestType;
};

export enum DynamicPartitionsRequestType {
  ADD_PARTITIONS = 'ADD_PARTITIONS',
  DELETE_PARTITIONS = 'DELETE_PARTITIONS',
}

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

export type FreshnessAutoMaterializeCondition = AutoMaterializeConditionWithDecisionType & {
  __typename: 'FreshnessAutoMaterializeCondition';
  decisionType: AutoMaterializeDecisionType;
  partitionKeysOrError: Maybe<PartitionKeysOrError>;
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
  autoMaterializePaused: Scalars['Boolean'];
  concurrencyLimits: Array<ConcurrencyKeyInfo>;
  daemonHealth: DaemonHealth;
  executablePath: Scalars['String'];
  hasCapturedLogManager: Scalars['Boolean'];
  hasInfo: Scalars['Boolean'];
  id: Scalars['String'];
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
  dynamicPartitionsRequestResults: Array<DynamicPartitionsRequestResult>;
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

export type JobWithOps = {
  __typename: 'JobWithOps';
  job: Job;
  opsUsing: Array<SolidHandle>;
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
  externalStderrUrl: Maybe<Scalars['String']>;
  externalStdoutUrl: Maybe<Scalars['String']>;
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

export type MaterializedPartitionRangeStatuses2D = {
  __typename: 'MaterializedPartitionRangeStatuses2D';
  primaryDimEndKey: Scalars['String'];
  primaryDimEndTime: Maybe<Scalars['Float']>;
  primaryDimStartKey: Scalars['String'];
  primaryDimStartTime: Maybe<Scalars['Float']>;
  secondaryDim: PartitionStatus1D;
};

export type MaxMaterializationsExceededAutoMaterializeCondition = AutoMaterializeConditionWithDecisionType & {
  __typename: 'MaxMaterializationsExceededAutoMaterializeCondition';
  decisionType: AutoMaterializeDecisionType;
  partitionKeysOrError: Maybe<PartitionKeysOrError>;
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

export type MissingAutoMaterializeCondition = AutoMaterializeConditionWithDecisionType & {
  __typename: 'MissingAutoMaterializeCondition';
  decisionType: AutoMaterializeDecisionType;
  partitionKeysOrError: Maybe<PartitionKeysOrError>;
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

export type MultiPartitionStatuses = {
  __typename: 'MultiPartitionStatuses';
  primaryDimensionName: Scalars['String'];
  ranges: Array<MaterializedPartitionRangeStatuses2D>;
};

export type NestedResourceEntry = {
  __typename: 'NestedResourceEntry';
  name: Scalars['String'];
  resource: Maybe<ResourceDetails>;
  type: NestedResourceType;
};

export enum NestedResourceType {
  ANONYMOUS = 'ANONYMOUS',
  TOP_LEVEL = 'TOP_LEVEL',
}

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

export type ParentMaterializedAutoMaterializeCondition = AutoMaterializeConditionWithDecisionType & {
  __typename: 'ParentMaterializedAutoMaterializeCondition';
  decisionType: AutoMaterializeDecisionType;
  partitionKeysOrError: Maybe<PartitionKeysOrError>;
};

export type ParentOutdatedAutoMaterializeCondition = AutoMaterializeConditionWithDecisionType & {
  __typename: 'ParentOutdatedAutoMaterializeCondition';
  decisionType: AutoMaterializeDecisionType;
  partitionKeysOrError: Maybe<PartitionKeysOrError>;
  waitingOnAssetKeys: Maybe<Array<AssetKey>>;
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
  assetBackfillData: Maybe<AssetBackfillData>;
  assetSelection: Maybe<Array<AssetKey>>;
  endTimestamp: Maybe<Scalars['Float']>;
  error: Maybe<PythonError>;
  fromFailure: Scalars['Boolean'];
  hasCancelPermission: Scalars['Boolean'];
  hasResumePermission: Scalars['Boolean'];
  id: Scalars['String'];
  isAssetBackfill: Scalars['Boolean'];
  isValidSerialization: Scalars['Boolean'];
  numCancelable: Scalars['Int'];
  numPartitions: Maybe<Scalars['Int']>;
  partitionNames: Maybe<Array<Scalars['String']>>;
  partitionSet: Maybe<PartitionSet>;
  partitionSetName: Maybe<Scalars['String']>;
  partitionStatusCounts: Array<PartitionStatusCounts>;
  partitionStatuses: Maybe<PartitionStatuses>;
  reexecutionSteps: Maybe<Array<Scalars['String']>>;
  runs: Array<Run>;
  status: BulkActionStatus;
  timestamp: Scalars['Float'];
  unfinishedRuns: Array<Run>;
  user: Maybe<Scalars['String']>;
};

export type PartitionBackfillRunsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionBackfillUnfinishedRunsArgs = {
  limit?: InputMaybe<Scalars['Int']>;
};

export type PartitionBackfillOrError = BackfillNotFoundError | PartitionBackfill | PythonError;

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
  type: PartitionDefinitionType;
};

export enum PartitionDefinitionType {
  DYNAMIC = 'DYNAMIC',
  MULTIPARTITIONED = 'MULTIPARTITIONED',
  STATIC = 'STATIC',
  TIME_WINDOW = 'TIME_WINDOW',
}

export type PartitionKeyRange = {
  __typename: 'PartitionKeyRange';
  end: Scalars['String'];
  start: Scalars['String'];
};

export type PartitionKeys = {
  __typename: 'PartitionKeys';
  partitionKeys: Array<Scalars['String']>;
};

export type PartitionKeysOrError = PartitionKeys | PartitionSubsetDeserializationError;

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
  numMaterializing: Scalars['Int'];
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

export type PartitionStatus1D = DefaultPartitionStatuses | TimePartitionStatuses;

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

export type PartitionSubsetDeserializationError = Error & {
  __typename: 'PartitionSubsetDeserializationError';
  message: Scalars['String'];
};

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
  assetKeysUsing: Array<AssetKey>;
  configFields: Array<ConfigTypeField>;
  configuredValues: Array<ConfiguredValue>;
  description: Maybe<Scalars['String']>;
  isTopLevel: Scalars['Boolean'];
  jobsOpsUsing: Array<JobWithOps>;
  name: Scalars['String'];
  nestedResources: Array<NestedResourceEntry>;
  parentResources: Array<NestedResourceEntry>;
  resourceType: Scalars['String'];
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
  rootDefaultYaml: Scalars['String'];
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
  assetSelection: Maybe<Array<AssetKey>>;
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
  category: StaleCauseCategory;
  dependency: Maybe<AssetKey>;
  key: AssetKey;
  reason: Scalars['String'];
};

export enum StaleCauseCategory {
  CODE = 'CODE',
  DATA = 'DATA',
  DEPENDENCIES = 'DEPENDENCIES',
}

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
  dynamicPartitionsRequests: Maybe<Array<DynamicPartitionRequest>>;
  error: Maybe<PythonError>;
  runRequests: Maybe<Array<RunRequest>>;
  skipReason: Maybe<Scalars['String']>;
};

export type TimePartitionRangeStatus = {
  __typename: 'TimePartitionRangeStatus';
  endKey: Scalars['String'];
  endTime: Scalars['Float'];
  startKey: Scalars['String'];
  startTime: Scalars['Float'];
  status: PartitionRangeStatus;
};

export type TimePartitionStatuses = {
  __typename: 'TimePartitionStatuses';
  ranges: Array<TimePartitionRangeStatus>;
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

export type UnpartitionedAssetStatus = {
  __typename: 'UnpartitionedAssetStatus';
  assetKey: AssetKey;
  failed: Scalars['Boolean'];
  inProgress: Scalars['Boolean'];
  materialized: Scalars['Boolean'];
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
  id: Scalars['String'];
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
  overrides?: Partial<AddDynamicPartitionSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AddDynamicPartitionSuccess'} & AddDynamicPartitionSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AddDynamicPartitionSuccess');
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
  overrides?: Partial<AlertFailureEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AlertFailureEvent'} & AlertFailureEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AlertFailureEvent');
  return {
    __typename: 'AlertFailureEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<AlertStartEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AlertStartEvent'} & AlertStartEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AlertStartEvent');
  return {
    __typename: 'AlertStartEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<AlertSuccessEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AlertSuccessEvent'} & AlertSuccessEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AlertSuccessEvent');
  return {
    __typename: 'AlertSuccessEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<ArrayConfigType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ArrayConfigType'} & ArrayConfigType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ArrayConfigType');
  return {
    __typename: 'ArrayConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'aliquam',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'omnis',
    ofType:
      overrides && overrides.hasOwnProperty('ofType')
        ? overrides.ofType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys') ? overrides.typeParamKeys! : [],
  };
};

export const buildAsset = (
  overrides?: Partial<Asset>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Asset'} & Asset => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Asset');
  return {
    __typename: 'Asset',
    assetMaterializations:
      overrides && overrides.hasOwnProperty('assetMaterializations')
        ? overrides.assetMaterializations!
        : [],
    assetObservations:
      overrides && overrides.hasOwnProperty('assetObservations')
        ? overrides.assetObservations!
        : [],
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : relationshipsToOmit.has('AssetNode')
        ? ({} as AssetNode)
        : buildAssetNode({}, relationshipsToOmit),
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'omnis',
    key:
      overrides && overrides.hasOwnProperty('key')
        ? overrides.key!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
  };
};

export const buildAssetBackfillData = (
  overrides?: Partial<AssetBackfillData>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetBackfillData'} & AssetBackfillData => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetBackfillData');
  return {
    __typename: 'AssetBackfillData',
    assetBackfillStatuses:
      overrides && overrides.hasOwnProperty('assetBackfillStatuses')
        ? overrides.assetBackfillStatuses!
        : [],
    rootAssetTargetedPartitions:
      overrides && overrides.hasOwnProperty('rootAssetTargetedPartitions')
        ? overrides.rootAssetTargetedPartitions!
        : [],
    rootAssetTargetedRanges:
      overrides && overrides.hasOwnProperty('rootAssetTargetedRanges')
        ? overrides.rootAssetTargetedRanges!
        : [],
  };
};

export const buildAssetConnection = (
  overrides?: Partial<AssetConnection>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetConnection'} & AssetConnection => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetConnection');
  return {
    __typename: 'AssetConnection',
    nodes: overrides && overrides.hasOwnProperty('nodes') ? overrides.nodes! : [],
  };
};

export const buildAssetDependency = (
  overrides?: Partial<AssetDependency>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetDependency'} & AssetDependency => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetDependency');
  return {
    __typename: 'AssetDependency',
    asset:
      overrides && overrides.hasOwnProperty('asset')
        ? overrides.asset!
        : relationshipsToOmit.has('AssetNode')
        ? ({} as AssetNode)
        : buildAssetNode({}, relationshipsToOmit),
    inputName:
      overrides && overrides.hasOwnProperty('inputName') ? overrides.inputName! : 'aspernatur',
  };
};

export const buildAssetFreshnessInfo = (
  overrides?: Partial<AssetFreshnessInfo>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetFreshnessInfo'} & AssetFreshnessInfo => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetFreshnessInfo');
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
  overrides?: Partial<AssetGroup>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetGroup'} & AssetGroup => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetGroup');
  return {
    __typename: 'AssetGroup',
    assetKeys: overrides && overrides.hasOwnProperty('assetKeys') ? overrides.assetKeys! : [],
    groupName: overrides && overrides.hasOwnProperty('groupName') ? overrides.groupName! : 'aut',
  };
};

export const buildAssetGroupSelector = (
  overrides?: Partial<AssetGroupSelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): AssetGroupSelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetGroupSelector');
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
  overrides?: Partial<AssetKey>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetKey'} & AssetKey => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetKey');
  return {
    __typename: 'AssetKey',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : [],
  };
};

export const buildAssetKeyInput = (
  overrides?: Partial<AssetKeyInput>,
  _relationshipsToOmit: Set<string> = new Set(),
): AssetKeyInput => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetKeyInput');
  return {
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : [],
  };
};

export const buildAssetLatestInfo = (
  overrides?: Partial<AssetLatestInfo>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetLatestInfo'} & AssetLatestInfo => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetLatestInfo');
  return {
    __typename: 'AssetLatestInfo',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    inProgressRunIds:
      overrides && overrides.hasOwnProperty('inProgressRunIds') ? overrides.inProgressRunIds! : [],
    latestMaterialization:
      overrides && overrides.hasOwnProperty('latestMaterialization')
        ? overrides.latestMaterialization!
        : relationshipsToOmit.has('MaterializationEvent')
        ? ({} as MaterializationEvent)
        : buildMaterializationEvent({}, relationshipsToOmit),
    latestRun:
      overrides && overrides.hasOwnProperty('latestRun')
        ? overrides.latestRun!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
    unstartedRunIds:
      overrides && overrides.hasOwnProperty('unstartedRunIds') ? overrides.unstartedRunIds! : [],
  };
};

export const buildAssetLineageInfo = (
  overrides?: Partial<AssetLineageInfo>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetLineageInfo'} & AssetLineageInfo => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetLineageInfo');
  return {
    __typename: 'AssetLineageInfo',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    partitions: overrides && overrides.hasOwnProperty('partitions') ? overrides.partitions! : [],
  };
};

export const buildAssetMaterializationPlannedEvent = (
  overrides?: Partial<AssetMaterializationPlannedEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetMaterializationPlannedEvent'} & AssetMaterializationPlannedEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetMaterializationPlannedEvent');
  return {
    __typename: 'AssetMaterializationPlannedEvent',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'amet',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'nesciunt',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'voluptas',
    runOrError:
      overrides && overrides.hasOwnProperty('runOrError')
        ? overrides.runOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'dolor',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'nulla',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'est',
  };
};

export const buildAssetMetadataEntry = (
  overrides?: Partial<AssetMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetMetadataEntry'} & AssetMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetMetadataEntry');
  return {
    __typename: 'AssetMetadataEntry',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quasi',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'iste',
  };
};

export const buildAssetNode = (
  overrides?: Partial<AssetNode>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetNode'} & AssetNode => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetNode');
  return {
    __typename: 'AssetNode',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    assetMaterializationUsedData:
      overrides && overrides.hasOwnProperty('assetMaterializationUsedData')
        ? overrides.assetMaterializationUsedData!
        : [],
    assetMaterializations:
      overrides && overrides.hasOwnProperty('assetMaterializations')
        ? overrides.assetMaterializations!
        : [],
    assetObservations:
      overrides && overrides.hasOwnProperty('assetObservations')
        ? overrides.assetObservations!
        : [],
    assetPartitionStatuses:
      overrides && overrides.hasOwnProperty('assetPartitionStatuses')
        ? overrides.assetPartitionStatuses!
        : relationshipsToOmit.has('DefaultPartitionStatuses')
        ? ({} as DefaultPartitionStatuses)
        : buildDefaultPartitionStatuses({}, relationshipsToOmit),
    autoMaterializePolicy:
      overrides && overrides.hasOwnProperty('autoMaterializePolicy')
        ? overrides.autoMaterializePolicy!
        : relationshipsToOmit.has('AutoMaterializePolicy')
        ? ({} as AutoMaterializePolicy)
        : buildAutoMaterializePolicy({}, relationshipsToOmit),
    computeKind:
      overrides && overrides.hasOwnProperty('computeKind') ? overrides.computeKind! : 'quasi',
    configField:
      overrides && overrides.hasOwnProperty('configField')
        ? overrides.configField!
        : relationshipsToOmit.has('ConfigTypeField')
        ? ({} as ConfigTypeField)
        : buildConfigTypeField({}, relationshipsToOmit),
    currentDataVersion:
      overrides && overrides.hasOwnProperty('currentDataVersion')
        ? overrides.currentDataVersion!
        : 'aperiam',
    dependedBy: overrides && overrides.hasOwnProperty('dependedBy') ? overrides.dependedBy! : [],
    dependedByKeys:
      overrides && overrides.hasOwnProperty('dependedByKeys') ? overrides.dependedByKeys! : [],
    dependencies:
      overrides && overrides.hasOwnProperty('dependencies') ? overrides.dependencies! : [],
    dependencyKeys:
      overrides && overrides.hasOwnProperty('dependencyKeys') ? overrides.dependencyKeys! : [],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'vitae',
    freshnessInfo:
      overrides && overrides.hasOwnProperty('freshnessInfo')
        ? overrides.freshnessInfo!
        : relationshipsToOmit.has('AssetFreshnessInfo')
        ? ({} as AssetFreshnessInfo)
        : buildAssetFreshnessInfo({}, relationshipsToOmit),
    freshnessPolicy:
      overrides && overrides.hasOwnProperty('freshnessPolicy')
        ? overrides.freshnessPolicy!
        : relationshipsToOmit.has('FreshnessPolicy')
        ? ({} as FreshnessPolicy)
        : buildFreshnessPolicy({}, relationshipsToOmit),
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
    jobNames: overrides && overrides.hasOwnProperty('jobNames') ? overrides.jobNames! : [],
    jobs: overrides && overrides.hasOwnProperty('jobs') ? overrides.jobs! : [],
    latestMaterializationByPartition:
      overrides && overrides.hasOwnProperty('latestMaterializationByPartition')
        ? overrides.latestMaterializationByPartition!
        : [],
    latestRunForPartition:
      overrides && overrides.hasOwnProperty('latestRunForPartition')
        ? overrides.latestRunForPartition!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    op:
      overrides && overrides.hasOwnProperty('op')
        ? overrides.op!
        : relationshipsToOmit.has('SolidDefinition')
        ? ({} as SolidDefinition)
        : buildSolidDefinition({}, relationshipsToOmit),
    opName: overrides && overrides.hasOwnProperty('opName') ? overrides.opName! : 'veritatis',
    opNames: overrides && overrides.hasOwnProperty('opNames') ? overrides.opNames! : [],
    opVersion:
      overrides && overrides.hasOwnProperty('opVersion') ? overrides.opVersion! : 'cupiditate',
    partitionDefinition:
      overrides && overrides.hasOwnProperty('partitionDefinition')
        ? overrides.partitionDefinition!
        : relationshipsToOmit.has('PartitionDefinition')
        ? ({} as PartitionDefinition)
        : buildPartitionDefinition({}, relationshipsToOmit),
    partitionKeys:
      overrides && overrides.hasOwnProperty('partitionKeys') ? overrides.partitionKeys! : [],
    partitionKeysByDimension:
      overrides && overrides.hasOwnProperty('partitionKeysByDimension')
        ? overrides.partitionKeysByDimension!
        : [],
    partitionStats:
      overrides && overrides.hasOwnProperty('partitionStats')
        ? overrides.partitionStats!
        : relationshipsToOmit.has('PartitionStats')
        ? ({} as PartitionStats)
        : buildPartitionStats({}, relationshipsToOmit),
    repository:
      overrides && overrides.hasOwnProperty('repository')
        ? overrides.repository!
        : relationshipsToOmit.has('Repository')
        ? ({} as Repository)
        : buildRepository({}, relationshipsToOmit),
    requiredResources:
      overrides && overrides.hasOwnProperty('requiredResources')
        ? overrides.requiredResources!
        : [],
    staleCauses: overrides && overrides.hasOwnProperty('staleCauses') ? overrides.staleCauses! : [],
    staleStatus:
      overrides && overrides.hasOwnProperty('staleStatus')
        ? overrides.staleStatus!
        : StaleStatus.FRESH,
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : relationshipsToOmit.has('DagsterType')
        ? ({} as DagsterType)
        : buildDagsterType({}, relationshipsToOmit),
  };
};

export const buildAssetNodeDefinitionCollision = (
  overrides?: Partial<AssetNodeDefinitionCollision>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetNodeDefinitionCollision'} & AssetNodeDefinitionCollision => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetNodeDefinitionCollision');
  return {
    __typename: 'AssetNodeDefinitionCollision',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    repositories:
      overrides && overrides.hasOwnProperty('repositories') ? overrides.repositories! : [],
  };
};

export const buildAssetNotFoundError = (
  overrides?: Partial<AssetNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetNotFoundError'} & AssetNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetNotFoundError');
  return {
    __typename: 'AssetNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'beatae',
  };
};

export const buildAssetPartitionsStatusCounts = (
  overrides?: Partial<AssetPartitionsStatusCounts>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetPartitionsStatusCounts'} & AssetPartitionsStatusCounts => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetPartitionsStatusCounts');
  return {
    __typename: 'AssetPartitionsStatusCounts',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    numPartitionsFailed:
      overrides && overrides.hasOwnProperty('numPartitionsFailed')
        ? overrides.numPartitionsFailed!
        : 6432,
    numPartitionsInProgress:
      overrides && overrides.hasOwnProperty('numPartitionsInProgress')
        ? overrides.numPartitionsInProgress!
        : 6636,
    numPartitionsMaterialized:
      overrides && overrides.hasOwnProperty('numPartitionsMaterialized')
        ? overrides.numPartitionsMaterialized!
        : 7555,
    numPartitionsTargeted:
      overrides && overrides.hasOwnProperty('numPartitionsTargeted')
        ? overrides.numPartitionsTargeted!
        : 5211,
  };
};

export const buildAssetWipeSuccess = (
  overrides?: Partial<AssetWipeSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AssetWipeSuccess'} & AssetWipeSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AssetWipeSuccess');
  return {
    __typename: 'AssetWipeSuccess',
    assetKeys: overrides && overrides.hasOwnProperty('assetKeys') ? overrides.assetKeys! : [],
  };
};

export const buildAutoMaterializeAssetEvaluationNeedsMigrationError = (
  overrides?: Partial<AutoMaterializeAssetEvaluationNeedsMigrationError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {
  __typename: 'AutoMaterializeAssetEvaluationNeedsMigrationError';
} & AutoMaterializeAssetEvaluationNeedsMigrationError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AutoMaterializeAssetEvaluationNeedsMigrationError');
  return {
    __typename: 'AutoMaterializeAssetEvaluationNeedsMigrationError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
  };
};

export const buildAutoMaterializeAssetEvaluationRecord = (
  overrides?: Partial<AutoMaterializeAssetEvaluationRecord>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AutoMaterializeAssetEvaluationRecord'} & AutoMaterializeAssetEvaluationRecord => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AutoMaterializeAssetEvaluationRecord');
  return {
    __typename: 'AutoMaterializeAssetEvaluationRecord',
    conditions: overrides && overrides.hasOwnProperty('conditions') ? overrides.conditions! : [],
    evaluationId:
      overrides && overrides.hasOwnProperty('evaluationId') ? overrides.evaluationId! : 9286,
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'f99fc708-761e-4261-a57a-393de7f89855',
    numDiscarded:
      overrides && overrides.hasOwnProperty('numDiscarded') ? overrides.numDiscarded! : 8280,
    numRequested:
      overrides && overrides.hasOwnProperty('numRequested') ? overrides.numRequested! : 2522,
    numSkipped: overrides && overrides.hasOwnProperty('numSkipped') ? overrides.numSkipped! : 6444,
    runIds: overrides && overrides.hasOwnProperty('runIds') ? overrides.runIds! : [],
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 0.19,
  };
};

export const buildAutoMaterializeAssetEvaluationRecords = (
  overrides?: Partial<AutoMaterializeAssetEvaluationRecords>,
  _relationshipsToOmit: Set<string> = new Set(),
): {
  __typename: 'AutoMaterializeAssetEvaluationRecords';
} & AutoMaterializeAssetEvaluationRecords => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AutoMaterializeAssetEvaluationRecords');
  return {
    __typename: 'AutoMaterializeAssetEvaluationRecords',
    currentEvaluationId:
      overrides && overrides.hasOwnProperty('currentEvaluationId')
        ? overrides.currentEvaluationId!
        : 9797,
    records: overrides && overrides.hasOwnProperty('records') ? overrides.records! : [],
  };
};

export const buildAutoMaterializeConditionWithDecisionType = (
  overrides?: Partial<AutoMaterializeConditionWithDecisionType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {
  __typename: 'AutoMaterializeConditionWithDecisionType';
} & AutoMaterializeConditionWithDecisionType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AutoMaterializeConditionWithDecisionType');
  return {
    __typename: 'AutoMaterializeConditionWithDecisionType',
    decisionType:
      overrides && overrides.hasOwnProperty('decisionType')
        ? overrides.decisionType!
        : AutoMaterializeDecisionType.DISCARD,
    partitionKeysOrError:
      overrides && overrides.hasOwnProperty('partitionKeysOrError')
        ? overrides.partitionKeysOrError!
        : relationshipsToOmit.has('PartitionKeys')
        ? ({} as PartitionKeys)
        : buildPartitionKeys({}, relationshipsToOmit),
  };
};

export const buildAutoMaterializePolicy = (
  overrides?: Partial<AutoMaterializePolicy>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'AutoMaterializePolicy'} & AutoMaterializePolicy => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('AutoMaterializePolicy');
  return {
    __typename: 'AutoMaterializePolicy',
    maxMaterializationsPerMinute:
      overrides && overrides.hasOwnProperty('maxMaterializationsPerMinute')
        ? overrides.maxMaterializationsPerMinute!
        : 9783,
    policyType:
      overrides && overrides.hasOwnProperty('policyType')
        ? overrides.policyType!
        : AutoMaterializePolicyType.EAGER,
  };
};

export const buildBackfillNotFoundError = (
  overrides?: Partial<BackfillNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'BackfillNotFoundError'} & BackfillNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('BackfillNotFoundError');
  return {
    __typename: 'BackfillNotFoundError',
    backfillId:
      overrides && overrides.hasOwnProperty('backfillId') ? overrides.backfillId! : 'nobis',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'est',
  };
};

export const buildBoolMetadataEntry = (
  overrides?: Partial<BoolMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'BoolMetadataEntry'} & BoolMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('BoolMetadataEntry');
  return {
    __typename: 'BoolMetadataEntry',
    boolValue: overrides && overrides.hasOwnProperty('boolValue') ? overrides.boolValue! : true,
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'illum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'dolorum',
  };
};

export const buildCancelBackfillSuccess = (
  overrides?: Partial<CancelBackfillSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'CancelBackfillSuccess'} & CancelBackfillSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('CancelBackfillSuccess');
  return {
    __typename: 'CancelBackfillSuccess',
    backfillId:
      overrides && overrides.hasOwnProperty('backfillId') ? overrides.backfillId! : 'animi',
  };
};

export const buildCapturedLogs = (
  overrides?: Partial<CapturedLogs>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'CapturedLogs'} & CapturedLogs => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('CapturedLogs');
  return {
    __typename: 'CapturedLogs',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'itaque',
    logKey: overrides && overrides.hasOwnProperty('logKey') ? overrides.logKey! : [],
    stderr: overrides && overrides.hasOwnProperty('stderr') ? overrides.stderr! : 'voluptatem',
    stdout: overrides && overrides.hasOwnProperty('stdout') ? overrides.stdout! : 'nesciunt',
  };
};

export const buildCapturedLogsMetadata = (
  overrides?: Partial<CapturedLogsMetadata>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'CapturedLogsMetadata'} & CapturedLogsMetadata => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('CapturedLogsMetadata');
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
  overrides?: Partial<CompositeConfigType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'CompositeConfigType'} & CompositeConfigType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('CompositeConfigType');
  return {
    __typename: 'CompositeConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'deleniti',
    fields: overrides && overrides.hasOwnProperty('fields') ? overrides.fields! : [],
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'nulla',
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys') ? overrides.typeParamKeys! : [],
  };
};

export const buildCompositeSolidDefinition = (
  overrides?: Partial<CompositeSolidDefinition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'CompositeSolidDefinition'} & CompositeSolidDefinition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('CompositeSolidDefinition');
  return {
    __typename: 'CompositeSolidDefinition',
    assetNodes: overrides && overrides.hasOwnProperty('assetNodes') ? overrides.assetNodes! : [],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'at',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '21c69675-bf11-4093-8cc2-4e3c64e910c9',
    inputDefinitions:
      overrides && overrides.hasOwnProperty('inputDefinitions') ? overrides.inputDefinitions! : [],
    inputMappings:
      overrides && overrides.hasOwnProperty('inputMappings') ? overrides.inputMappings! : [],
    metadata: overrides && overrides.hasOwnProperty('metadata') ? overrides.metadata! : [],
    modes: overrides && overrides.hasOwnProperty('modes') ? overrides.modes! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'consequatur',
    outputDefinitions:
      overrides && overrides.hasOwnProperty('outputDefinitions')
        ? overrides.outputDefinitions!
        : [],
    outputMappings:
      overrides && overrides.hasOwnProperty('outputMappings') ? overrides.outputMappings! : [],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : relationshipsToOmit.has('SolidHandle')
        ? ({} as SolidHandle)
        : buildSolidHandle({}, relationshipsToOmit),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles') ? overrides.solidHandles! : [],
    solids: overrides && overrides.hasOwnProperty('solids') ? overrides.solids! : [],
  };
};

export const buildComputeLogFile = (
  overrides?: Partial<ComputeLogFile>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ComputeLogFile'} & ComputeLogFile => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ComputeLogFile');
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
  overrides?: Partial<ComputeLogs>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ComputeLogs'} & ComputeLogs => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ComputeLogs');
  return {
    __typename: 'ComputeLogs',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'est',
    stderr:
      overrides && overrides.hasOwnProperty('stderr')
        ? overrides.stderr!
        : relationshipsToOmit.has('ComputeLogFile')
        ? ({} as ComputeLogFile)
        : buildComputeLogFile({}, relationshipsToOmit),
    stdout:
      overrides && overrides.hasOwnProperty('stdout')
        ? overrides.stdout!
        : relationshipsToOmit.has('ComputeLogFile')
        ? ({} as ComputeLogFile)
        : buildComputeLogFile({}, relationshipsToOmit),
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'cum',
  };
};

export const buildConcurrencyKeyInfo = (
  overrides?: Partial<ConcurrencyKeyInfo>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ConcurrencyKeyInfo'} & ConcurrencyKeyInfo => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ConcurrencyKeyInfo');
  return {
    __typename: 'ConcurrencyKeyInfo',
    activeRunIds:
      overrides && overrides.hasOwnProperty('activeRunIds') ? overrides.activeRunIds! : [],
    activeSlotCount:
      overrides && overrides.hasOwnProperty('activeSlotCount') ? overrides.activeSlotCount! : 1206,
    assignedStepCount:
      overrides && overrides.hasOwnProperty('assignedStepCount')
        ? overrides.assignedStepCount!
        : 3480,
    assignedStepRunIds:
      overrides && overrides.hasOwnProperty('assignedStepRunIds')
        ? overrides.assignedStepRunIds!
        : [],
    concurrencyKey:
      overrides && overrides.hasOwnProperty('concurrencyKey') ? overrides.concurrencyKey! : 'quasi',
    pendingStepCount:
      overrides && overrides.hasOwnProperty('pendingStepCount') ? overrides.pendingStepCount! : 370,
    pendingStepRunIds:
      overrides && overrides.hasOwnProperty('pendingStepRunIds')
        ? overrides.pendingStepRunIds!
        : [],
    slotCount: overrides && overrides.hasOwnProperty('slotCount') ? overrides.slotCount! : 455,
  };
};

export const buildConfigType = (
  overrides?: Partial<ConfigType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ConfigType'} & ConfigType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ConfigType');
  return {
    __typename: 'ConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'nostrum',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'earum',
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys') ? overrides.typeParamKeys! : [],
  };
};

export const buildConfigTypeField = (
  overrides?: Partial<ConfigTypeField>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ConfigTypeField'} & ConfigTypeField => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ConfigTypeField');
  return {
    __typename: 'ConfigTypeField',
    configType:
      overrides && overrides.hasOwnProperty('configType')
        ? overrides.configType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
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
  overrides?: Partial<ConfigTypeNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ConfigTypeNotFoundError'} & ConfigTypeNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ConfigTypeNotFoundError');
  return {
    __typename: 'ConfigTypeNotFoundError',
    configTypeName:
      overrides && overrides.hasOwnProperty('configTypeName') ? overrides.configTypeName! : 'ullam',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'suscipit',
    pipeline:
      overrides && overrides.hasOwnProperty('pipeline')
        ? overrides.pipeline!
        : relationshipsToOmit.has('Pipeline')
        ? ({} as Pipeline)
        : buildPipeline({}, relationshipsToOmit),
  };
};

export const buildConfiguredValue = (
  overrides?: Partial<ConfiguredValue>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ConfiguredValue'} & ConfiguredValue => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ConfiguredValue');
  return {
    __typename: 'ConfiguredValue',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'ipsam',
    type:
      overrides && overrides.hasOwnProperty('type') ? overrides.type! : ConfiguredValueType.ENV_VAR,
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'distinctio',
  };
};

export const buildConflictingExecutionParamsError = (
  overrides?: Partial<ConflictingExecutionParamsError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ConflictingExecutionParamsError'} & ConflictingExecutionParamsError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ConflictingExecutionParamsError');
  return {
    __typename: 'ConflictingExecutionParamsError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'pariatur',
  };
};

export const buildDaemonHealth = (
  overrides?: Partial<DaemonHealth>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DaemonHealth'} & DaemonHealth => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DaemonHealth');
  return {
    __typename: 'DaemonHealth',
    allDaemonStatuses:
      overrides && overrides.hasOwnProperty('allDaemonStatuses')
        ? overrides.allDaemonStatuses!
        : [],
    daemonStatus:
      overrides && overrides.hasOwnProperty('daemonStatus')
        ? overrides.daemonStatus!
        : relationshipsToOmit.has('DaemonStatus')
        ? ({} as DaemonStatus)
        : buildDaemonStatus({}, relationshipsToOmit),
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'omnis',
  };
};

export const buildDaemonStatus = (
  overrides?: Partial<DaemonStatus>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DaemonStatus'} & DaemonStatus => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DaemonStatus');
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
        : [],
    lastHeartbeatTime:
      overrides && overrides.hasOwnProperty('lastHeartbeatTime')
        ? overrides.lastHeartbeatTime!
        : 8.69,
    required: overrides && overrides.hasOwnProperty('required') ? overrides.required! : false,
  };
};

export const buildDagitMutation = (
  overrides?: Partial<DagitMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DagitMutation'} & DagitMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DagitMutation');
  return {
    __typename: 'DagitMutation',
    addDynamicPartition:
      overrides && overrides.hasOwnProperty('addDynamicPartition')
        ? overrides.addDynamicPartition!
        : relationshipsToOmit.has('AddDynamicPartitionSuccess')
        ? ({} as AddDynamicPartitionSuccess)
        : buildAddDynamicPartitionSuccess({}, relationshipsToOmit),
    cancelPartitionBackfill:
      overrides && overrides.hasOwnProperty('cancelPartitionBackfill')
        ? overrides.cancelPartitionBackfill!
        : relationshipsToOmit.has('CancelBackfillSuccess')
        ? ({} as CancelBackfillSuccess)
        : buildCancelBackfillSuccess({}, relationshipsToOmit),
    deletePipelineRun:
      overrides && overrides.hasOwnProperty('deletePipelineRun')
        ? overrides.deletePipelineRun!
        : relationshipsToOmit.has('DeletePipelineRunSuccess')
        ? ({} as DeletePipelineRunSuccess)
        : buildDeletePipelineRunSuccess({}, relationshipsToOmit),
    deleteRun:
      overrides && overrides.hasOwnProperty('deleteRun')
        ? overrides.deleteRun!
        : relationshipsToOmit.has('DeletePipelineRunSuccess')
        ? ({} as DeletePipelineRunSuccess)
        : buildDeletePipelineRunSuccess({}, relationshipsToOmit),
    freeConcurrencySlotsForRun:
      overrides && overrides.hasOwnProperty('freeConcurrencySlotsForRun')
        ? overrides.freeConcurrencySlotsForRun!
        : false,
    launchPartitionBackfill:
      overrides && overrides.hasOwnProperty('launchPartitionBackfill')
        ? overrides.launchPartitionBackfill!
        : relationshipsToOmit.has('ConflictingExecutionParamsError')
        ? ({} as ConflictingExecutionParamsError)
        : buildConflictingExecutionParamsError({}, relationshipsToOmit),
    launchPipelineExecution:
      overrides && overrides.hasOwnProperty('launchPipelineExecution')
        ? overrides.launchPipelineExecution!
        : relationshipsToOmit.has('ConflictingExecutionParamsError')
        ? ({} as ConflictingExecutionParamsError)
        : buildConflictingExecutionParamsError({}, relationshipsToOmit),
    launchPipelineReexecution:
      overrides && overrides.hasOwnProperty('launchPipelineReexecution')
        ? overrides.launchPipelineReexecution!
        : relationshipsToOmit.has('ConflictingExecutionParamsError')
        ? ({} as ConflictingExecutionParamsError)
        : buildConflictingExecutionParamsError({}, relationshipsToOmit),
    launchRun:
      overrides && overrides.hasOwnProperty('launchRun')
        ? overrides.launchRun!
        : relationshipsToOmit.has('ConflictingExecutionParamsError')
        ? ({} as ConflictingExecutionParamsError)
        : buildConflictingExecutionParamsError({}, relationshipsToOmit),
    launchRunReexecution:
      overrides && overrides.hasOwnProperty('launchRunReexecution')
        ? overrides.launchRunReexecution!
        : relationshipsToOmit.has('ConflictingExecutionParamsError')
        ? ({} as ConflictingExecutionParamsError)
        : buildConflictingExecutionParamsError({}, relationshipsToOmit),
    logTelemetry:
      overrides && overrides.hasOwnProperty('logTelemetry')
        ? overrides.logTelemetry!
        : relationshipsToOmit.has('LogTelemetrySuccess')
        ? ({} as LogTelemetrySuccess)
        : buildLogTelemetrySuccess({}, relationshipsToOmit),
    reloadRepositoryLocation:
      overrides && overrides.hasOwnProperty('reloadRepositoryLocation')
        ? overrides.reloadRepositoryLocation!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    reloadWorkspace:
      overrides && overrides.hasOwnProperty('reloadWorkspace')
        ? overrides.reloadWorkspace!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    resumePartitionBackfill:
      overrides && overrides.hasOwnProperty('resumePartitionBackfill')
        ? overrides.resumePartitionBackfill!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    scheduleDryRun:
      overrides && overrides.hasOwnProperty('scheduleDryRun')
        ? overrides.scheduleDryRun!
        : relationshipsToOmit.has('DryRunInstigationTick')
        ? ({} as DryRunInstigationTick)
        : buildDryRunInstigationTick({}, relationshipsToOmit),
    sensorDryRun:
      overrides && overrides.hasOwnProperty('sensorDryRun')
        ? overrides.sensorDryRun!
        : relationshipsToOmit.has('DryRunInstigationTick')
        ? ({} as DryRunInstigationTick)
        : buildDryRunInstigationTick({}, relationshipsToOmit),
    setAutoMaterializePaused:
      overrides && overrides.hasOwnProperty('setAutoMaterializePaused')
        ? overrides.setAutoMaterializePaused!
        : true,
    setConcurrencyLimit:
      overrides && overrides.hasOwnProperty('setConcurrencyLimit')
        ? overrides.setConcurrencyLimit!
        : true,
    setNuxSeen: overrides && overrides.hasOwnProperty('setNuxSeen') ? overrides.setNuxSeen! : true,
    setSensorCursor:
      overrides && overrides.hasOwnProperty('setSensorCursor')
        ? overrides.setSensorCursor!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    shutdownRepositoryLocation:
      overrides && overrides.hasOwnProperty('shutdownRepositoryLocation')
        ? overrides.shutdownRepositoryLocation!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    startSchedule:
      overrides && overrides.hasOwnProperty('startSchedule')
        ? overrides.startSchedule!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    startSensor:
      overrides && overrides.hasOwnProperty('startSensor')
        ? overrides.startSensor!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    stopRunningSchedule:
      overrides && overrides.hasOwnProperty('stopRunningSchedule')
        ? overrides.stopRunningSchedule!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    stopSensor:
      overrides && overrides.hasOwnProperty('stopSensor')
        ? overrides.stopSensor!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    terminatePipelineExecution:
      overrides && overrides.hasOwnProperty('terminatePipelineExecution')
        ? overrides.terminatePipelineExecution!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    terminateRun:
      overrides && overrides.hasOwnProperty('terminateRun')
        ? overrides.terminateRun!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    wipeAssets:
      overrides && overrides.hasOwnProperty('wipeAssets')
        ? overrides.wipeAssets!
        : relationshipsToOmit.has('AssetNotFoundError')
        ? ({} as AssetNotFoundError)
        : buildAssetNotFoundError({}, relationshipsToOmit),
  };
};

export const buildDagitQuery = (
  overrides?: Partial<DagitQuery>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DagitQuery'} & DagitQuery => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DagitQuery');
  return {
    __typename: 'DagitQuery',
    allTopLevelResourceDetailsOrError:
      overrides && overrides.hasOwnProperty('allTopLevelResourceDetailsOrError')
        ? overrides.allTopLevelResourceDetailsOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    assetNodeDefinitionCollisions:
      overrides && overrides.hasOwnProperty('assetNodeDefinitionCollisions')
        ? overrides.assetNodeDefinitionCollisions!
        : [],
    assetNodeOrError:
      overrides && overrides.hasOwnProperty('assetNodeOrError')
        ? overrides.assetNodeOrError!
        : relationshipsToOmit.has('AssetNode')
        ? ({} as AssetNode)
        : buildAssetNode({}, relationshipsToOmit),
    assetNodes: overrides && overrides.hasOwnProperty('assetNodes') ? overrides.assetNodes! : [],
    assetOrError:
      overrides && overrides.hasOwnProperty('assetOrError')
        ? overrides.assetOrError!
        : relationshipsToOmit.has('Asset')
        ? ({} as Asset)
        : buildAsset({}, relationshipsToOmit),
    assetsLatestInfo:
      overrides && overrides.hasOwnProperty('assetsLatestInfo') ? overrides.assetsLatestInfo! : [],
    assetsOrError:
      overrides && overrides.hasOwnProperty('assetsOrError')
        ? overrides.assetsOrError!
        : relationshipsToOmit.has('AssetConnection')
        ? ({} as AssetConnection)
        : buildAssetConnection({}, relationshipsToOmit),
    autoMaterializeAssetEvaluationsOrError:
      overrides && overrides.hasOwnProperty('autoMaterializeAssetEvaluationsOrError')
        ? overrides.autoMaterializeAssetEvaluationsOrError!
        : relationshipsToOmit.has('AutoMaterializeAssetEvaluationNeedsMigrationError')
        ? ({} as AutoMaterializeAssetEvaluationNeedsMigrationError)
        : buildAutoMaterializeAssetEvaluationNeedsMigrationError({}, relationshipsToOmit),
    capturedLogs:
      overrides && overrides.hasOwnProperty('capturedLogs')
        ? overrides.capturedLogs!
        : relationshipsToOmit.has('CapturedLogs')
        ? ({} as CapturedLogs)
        : buildCapturedLogs({}, relationshipsToOmit),
    capturedLogsMetadata:
      overrides && overrides.hasOwnProperty('capturedLogsMetadata')
        ? overrides.capturedLogsMetadata!
        : relationshipsToOmit.has('CapturedLogsMetadata')
        ? ({} as CapturedLogsMetadata)
        : buildCapturedLogsMetadata({}, relationshipsToOmit),
    executionPlanOrError:
      overrides && overrides.hasOwnProperty('executionPlanOrError')
        ? overrides.executionPlanOrError!
        : relationshipsToOmit.has('ExecutionPlan')
        ? ({} as ExecutionPlan)
        : buildExecutionPlan({}, relationshipsToOmit),
    graphOrError:
      overrides && overrides.hasOwnProperty('graphOrError')
        ? overrides.graphOrError!
        : relationshipsToOmit.has('Graph')
        ? ({} as Graph)
        : buildGraph({}, relationshipsToOmit),
    instance:
      overrides && overrides.hasOwnProperty('instance')
        ? overrides.instance!
        : relationshipsToOmit.has('Instance')
        ? ({} as Instance)
        : buildInstance({}, relationshipsToOmit),
    instigationStateOrError:
      overrides && overrides.hasOwnProperty('instigationStateOrError')
        ? overrides.instigationStateOrError!
        : relationshipsToOmit.has('InstigationState')
        ? ({} as InstigationState)
        : buildInstigationState({}, relationshipsToOmit),
    isPipelineConfigValid:
      overrides && overrides.hasOwnProperty('isPipelineConfigValid')
        ? overrides.isPipelineConfigValid!
        : relationshipsToOmit.has('InvalidSubsetError')
        ? ({} as InvalidSubsetError)
        : buildInvalidSubsetError({}, relationshipsToOmit),
    locationStatusesOrError:
      overrides && overrides.hasOwnProperty('locationStatusesOrError')
        ? overrides.locationStatusesOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    logsForRun:
      overrides && overrides.hasOwnProperty('logsForRun')
        ? overrides.logsForRun!
        : relationshipsToOmit.has('EventConnection')
        ? ({} as EventConnection)
        : buildEventConnection({}, relationshipsToOmit),
    partitionBackfillOrError:
      overrides && overrides.hasOwnProperty('partitionBackfillOrError')
        ? overrides.partitionBackfillOrError!
        : relationshipsToOmit.has('BackfillNotFoundError')
        ? ({} as BackfillNotFoundError)
        : buildBackfillNotFoundError({}, relationshipsToOmit),
    partitionBackfillsOrError:
      overrides && overrides.hasOwnProperty('partitionBackfillsOrError')
        ? overrides.partitionBackfillsOrError!
        : relationshipsToOmit.has('PartitionBackfills')
        ? ({} as PartitionBackfills)
        : buildPartitionBackfills({}, relationshipsToOmit),
    partitionSetOrError:
      overrides && overrides.hasOwnProperty('partitionSetOrError')
        ? overrides.partitionSetOrError!
        : relationshipsToOmit.has('PartitionSet')
        ? ({} as PartitionSet)
        : buildPartitionSet({}, relationshipsToOmit),
    partitionSetsOrError:
      overrides && overrides.hasOwnProperty('partitionSetsOrError')
        ? overrides.partitionSetsOrError!
        : relationshipsToOmit.has('PartitionSets')
        ? ({} as PartitionSets)
        : buildPartitionSets({}, relationshipsToOmit),
    permissions: overrides && overrides.hasOwnProperty('permissions') ? overrides.permissions! : [],
    pipelineOrError:
      overrides && overrides.hasOwnProperty('pipelineOrError')
        ? overrides.pipelineOrError!
        : relationshipsToOmit.has('InvalidSubsetError')
        ? ({} as InvalidSubsetError)
        : buildInvalidSubsetError({}, relationshipsToOmit),
    pipelineRunOrError:
      overrides && overrides.hasOwnProperty('pipelineRunOrError')
        ? overrides.pipelineRunOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    pipelineRunsOrError:
      overrides && overrides.hasOwnProperty('pipelineRunsOrError')
        ? overrides.pipelineRunsOrError!
        : relationshipsToOmit.has('InvalidPipelineRunsFilterError')
        ? ({} as InvalidPipelineRunsFilterError)
        : buildInvalidPipelineRunsFilterError({}, relationshipsToOmit),
    pipelineSnapshotOrError:
      overrides && overrides.hasOwnProperty('pipelineSnapshotOrError')
        ? overrides.pipelineSnapshotOrError!
        : relationshipsToOmit.has('PipelineNotFoundError')
        ? ({} as PipelineNotFoundError)
        : buildPipelineNotFoundError({}, relationshipsToOmit),
    repositoriesOrError:
      overrides && overrides.hasOwnProperty('repositoriesOrError')
        ? overrides.repositoriesOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    repositoryOrError:
      overrides && overrides.hasOwnProperty('repositoryOrError')
        ? overrides.repositoryOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    runConfigSchemaOrError:
      overrides && overrides.hasOwnProperty('runConfigSchemaOrError')
        ? overrides.runConfigSchemaOrError!
        : relationshipsToOmit.has('InvalidSubsetError')
        ? ({} as InvalidSubsetError)
        : buildInvalidSubsetError({}, relationshipsToOmit),
    runGroupOrError:
      overrides && overrides.hasOwnProperty('runGroupOrError')
        ? overrides.runGroupOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    runGroupsOrError:
      overrides && overrides.hasOwnProperty('runGroupsOrError')
        ? overrides.runGroupsOrError!
        : relationshipsToOmit.has('RunGroupsOrError')
        ? ({} as RunGroupsOrError)
        : buildRunGroupsOrError({}, relationshipsToOmit),
    runOrError:
      overrides && overrides.hasOwnProperty('runOrError')
        ? overrides.runOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    runTagKeysOrError:
      overrides && overrides.hasOwnProperty('runTagKeysOrError')
        ? overrides.runTagKeysOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    runTagsOrError:
      overrides && overrides.hasOwnProperty('runTagsOrError')
        ? overrides.runTagsOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    runsOrError:
      overrides && overrides.hasOwnProperty('runsOrError')
        ? overrides.runsOrError!
        : relationshipsToOmit.has('InvalidPipelineRunsFilterError')
        ? ({} as InvalidPipelineRunsFilterError)
        : buildInvalidPipelineRunsFilterError({}, relationshipsToOmit),
    scheduleOrError:
      overrides && overrides.hasOwnProperty('scheduleOrError')
        ? overrides.scheduleOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    scheduler:
      overrides && overrides.hasOwnProperty('scheduler')
        ? overrides.scheduler!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    schedulesOrError:
      overrides && overrides.hasOwnProperty('schedulesOrError')
        ? overrides.schedulesOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    sensorOrError:
      overrides && overrides.hasOwnProperty('sensorOrError')
        ? overrides.sensorOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    sensorsOrError:
      overrides && overrides.hasOwnProperty('sensorsOrError')
        ? overrides.sensorsOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    shouldShowNux:
      overrides && overrides.hasOwnProperty('shouldShowNux') ? overrides.shouldShowNux! : true,
    test:
      overrides && overrides.hasOwnProperty('test')
        ? overrides.test!
        : relationshipsToOmit.has('TestFields')
        ? ({} as TestFields)
        : buildTestFields({}, relationshipsToOmit),
    topLevelResourceDetailsOrError:
      overrides && overrides.hasOwnProperty('topLevelResourceDetailsOrError')
        ? overrides.topLevelResourceDetailsOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    unloadableInstigationStatesOrError:
      overrides && overrides.hasOwnProperty('unloadableInstigationStatesOrError')
        ? overrides.unloadableInstigationStatesOrError!
        : relationshipsToOmit.has('InstigationStates')
        ? ({} as InstigationStates)
        : buildInstigationStates({}, relationshipsToOmit),
    utilizedEnvVarsOrError:
      overrides && overrides.hasOwnProperty('utilizedEnvVarsOrError')
        ? overrides.utilizedEnvVarsOrError!
        : relationshipsToOmit.has('EnvVarWithConsumersList')
        ? ({} as EnvVarWithConsumersList)
        : buildEnvVarWithConsumersList({}, relationshipsToOmit),
    version: overrides && overrides.hasOwnProperty('version') ? overrides.version! : 'sed',
    workspaceOrError:
      overrides && overrides.hasOwnProperty('workspaceOrError')
        ? overrides.workspaceOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildDagitSubscription = (
  overrides?: Partial<DagitSubscription>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DagitSubscription'} & DagitSubscription => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DagitSubscription');
  return {
    __typename: 'DagitSubscription',
    capturedLogs:
      overrides && overrides.hasOwnProperty('capturedLogs')
        ? overrides.capturedLogs!
        : relationshipsToOmit.has('CapturedLogs')
        ? ({} as CapturedLogs)
        : buildCapturedLogs({}, relationshipsToOmit),
    computeLogs:
      overrides && overrides.hasOwnProperty('computeLogs')
        ? overrides.computeLogs!
        : relationshipsToOmit.has('ComputeLogFile')
        ? ({} as ComputeLogFile)
        : buildComputeLogFile({}, relationshipsToOmit),
    locationStateChangeEvents:
      overrides && overrides.hasOwnProperty('locationStateChangeEvents')
        ? overrides.locationStateChangeEvents!
        : relationshipsToOmit.has('LocationStateChangeSubscription')
        ? ({} as LocationStateChangeSubscription)
        : buildLocationStateChangeSubscription({}, relationshipsToOmit),
    pipelineRunLogs:
      overrides && overrides.hasOwnProperty('pipelineRunLogs')
        ? overrides.pipelineRunLogs!
        : relationshipsToOmit.has('PipelineRunLogsSubscriptionFailure')
        ? ({} as PipelineRunLogsSubscriptionFailure)
        : buildPipelineRunLogsSubscriptionFailure({}, relationshipsToOmit),
  };
};

export const buildDagsterLibraryVersion = (
  overrides?: Partial<DagsterLibraryVersion>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DagsterLibraryVersion'} & DagsterLibraryVersion => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DagsterLibraryVersion');
  return {
    __typename: 'DagsterLibraryVersion',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'et',
    version: overrides && overrides.hasOwnProperty('version') ? overrides.version! : 'qui',
  };
};

export const buildDagsterType = (
  overrides?: Partial<DagsterType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DagsterType'} & DagsterType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DagsterType');
  return {
    __typename: 'DagsterType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'sed',
    displayName:
      overrides && overrides.hasOwnProperty('displayName') ? overrides.displayName! : 'consequatur',
    innerTypes: overrides && overrides.hasOwnProperty('innerTypes') ? overrides.innerTypes! : [],
    inputSchemaType:
      overrides && overrides.hasOwnProperty('inputSchemaType')
        ? overrides.inputSchemaType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    isBuiltin: overrides && overrides.hasOwnProperty('isBuiltin') ? overrides.isBuiltin! : true,
    isList: overrides && overrides.hasOwnProperty('isList') ? overrides.isList! : true,
    isNothing: overrides && overrides.hasOwnProperty('isNothing') ? overrides.isNothing! : true,
    isNullable: overrides && overrides.hasOwnProperty('isNullable') ? overrides.isNullable! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'sed',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'eum',
    outputSchemaType:
      overrides && overrides.hasOwnProperty('outputSchemaType')
        ? overrides.outputSchemaType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
  };
};

export const buildDagsterTypeNotFoundError = (
  overrides?: Partial<DagsterTypeNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DagsterTypeNotFoundError'} & DagsterTypeNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DagsterTypeNotFoundError');
  return {
    __typename: 'DagsterTypeNotFoundError',
    dagsterTypeName:
      overrides && overrides.hasOwnProperty('dagsterTypeName')
        ? overrides.dagsterTypeName!
        : 'quia',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'dolore',
  };
};

export const buildDefaultPartitionStatuses = (
  overrides?: Partial<DefaultPartitionStatuses>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DefaultPartitionStatuses'} & DefaultPartitionStatuses => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DefaultPartitionStatuses');
  return {
    __typename: 'DefaultPartitionStatuses',
    failedPartitions:
      overrides && overrides.hasOwnProperty('failedPartitions') ? overrides.failedPartitions! : [],
    materializedPartitions:
      overrides && overrides.hasOwnProperty('materializedPartitions')
        ? overrides.materializedPartitions!
        : [],
    materializingPartitions:
      overrides && overrides.hasOwnProperty('materializingPartitions')
        ? overrides.materializingPartitions!
        : [],
    unmaterializedPartitions:
      overrides && overrides.hasOwnProperty('unmaterializedPartitions')
        ? overrides.unmaterializedPartitions!
        : [],
  };
};

export const buildDeletePipelineRunSuccess = (
  overrides?: Partial<DeletePipelineRunSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DeletePipelineRunSuccess'} & DeletePipelineRunSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DeletePipelineRunSuccess');
  return {
    __typename: 'DeletePipelineRunSuccess',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'ipsum',
  };
};

export const buildDeleteRunMutation = (
  overrides?: Partial<DeleteRunMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DeleteRunMutation'} & DeleteRunMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DeleteRunMutation');
  return {
    __typename: 'DeleteRunMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('DeletePipelineRunSuccess')
        ? ({} as DeletePipelineRunSuccess)
        : buildDeletePipelineRunSuccess({}, relationshipsToOmit),
  };
};

export const buildDimensionDefinitionType = (
  overrides?: Partial<DimensionDefinitionType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DimensionDefinitionType'} & DimensionDefinitionType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DimensionDefinitionType');
  return {
    __typename: 'DimensionDefinitionType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'aut',
    dynamicPartitionsDefinitionName:
      overrides && overrides.hasOwnProperty('dynamicPartitionsDefinitionName')
        ? overrides.dynamicPartitionsDefinitionName!
        : 'qui',
    isPrimaryDimension:
      overrides && overrides.hasOwnProperty('isPrimaryDimension')
        ? overrides.isPrimaryDimension!
        : true,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'vel',
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : PartitionDefinitionType.DYNAMIC,
  };
};

export const buildDimensionPartitionKeys = (
  overrides?: Partial<DimensionPartitionKeys>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DimensionPartitionKeys'} & DimensionPartitionKeys => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DimensionPartitionKeys');
  return {
    __typename: 'DimensionPartitionKeys',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'id',
    partitionKeys:
      overrides && overrides.hasOwnProperty('partitionKeys') ? overrides.partitionKeys! : [],
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : PartitionDefinitionType.DYNAMIC,
  };
};

export const buildDisplayableEvent = (
  overrides?: Partial<DisplayableEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DisplayableEvent'} & DisplayableEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DisplayableEvent');
  return {
    __typename: 'DisplayableEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'pariatur',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'ipsa',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
  };
};

export const buildDownstreamFreshnessAutoMaterializeCondition = (
  overrides?: Partial<DownstreamFreshnessAutoMaterializeCondition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {
  __typename: 'DownstreamFreshnessAutoMaterializeCondition';
} & DownstreamFreshnessAutoMaterializeCondition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DownstreamFreshnessAutoMaterializeCondition');
  return {
    __typename: 'DownstreamFreshnessAutoMaterializeCondition',
    decisionType:
      overrides && overrides.hasOwnProperty('decisionType')
        ? overrides.decisionType!
        : AutoMaterializeDecisionType.DISCARD,
    partitionKeysOrError:
      overrides && overrides.hasOwnProperty('partitionKeysOrError')
        ? overrides.partitionKeysOrError!
        : relationshipsToOmit.has('PartitionKeys')
        ? ({} as PartitionKeys)
        : buildPartitionKeys({}, relationshipsToOmit),
  };
};

export const buildDryRunInstigationTick = (
  overrides?: Partial<DryRunInstigationTick>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DryRunInstigationTick'} & DryRunInstigationTick => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DryRunInstigationTick');
  return {
    __typename: 'DryRunInstigationTick',
    evaluationResult:
      overrides && overrides.hasOwnProperty('evaluationResult')
        ? overrides.evaluationResult!
        : relationshipsToOmit.has('TickEvaluation')
        ? ({} as TickEvaluation)
        : buildTickEvaluation({}, relationshipsToOmit),
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 7.53,
  };
};

export const buildDryRunInstigationTicks = (
  overrides?: Partial<DryRunInstigationTicks>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DryRunInstigationTicks'} & DryRunInstigationTicks => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DryRunInstigationTicks');
  return {
    __typename: 'DryRunInstigationTicks',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 0.85,
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildDuplicateDynamicPartitionError = (
  overrides?: Partial<DuplicateDynamicPartitionError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DuplicateDynamicPartitionError'} & DuplicateDynamicPartitionError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DuplicateDynamicPartitionError');
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

export const buildDynamicPartitionRequest = (
  overrides?: Partial<DynamicPartitionRequest>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DynamicPartitionRequest'} & DynamicPartitionRequest => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DynamicPartitionRequest');
  return {
    __typename: 'DynamicPartitionRequest',
    partitionKeys:
      overrides && overrides.hasOwnProperty('partitionKeys') ? overrides.partitionKeys! : [],
    partitionsDefName:
      overrides && overrides.hasOwnProperty('partitionsDefName')
        ? overrides.partitionsDefName!
        : 'ut',
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : DynamicPartitionsRequestType.ADD_PARTITIONS,
  };
};

export const buildDynamicPartitionsRequestResult = (
  overrides?: Partial<DynamicPartitionsRequestResult>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'DynamicPartitionsRequestResult'} & DynamicPartitionsRequestResult => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('DynamicPartitionsRequestResult');
  return {
    __typename: 'DynamicPartitionsRequestResult',
    partitionKeys:
      overrides && overrides.hasOwnProperty('partitionKeys') ? overrides.partitionKeys! : [],
    partitionsDefName:
      overrides && overrides.hasOwnProperty('partitionsDefName')
        ? overrides.partitionsDefName!
        : 'necessitatibus',
    skippedPartitionKeys:
      overrides && overrides.hasOwnProperty('skippedPartitionKeys')
        ? overrides.skippedPartitionKeys!
        : [],
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : DynamicPartitionsRequestType.ADD_PARTITIONS,
  };
};

export const buildEngineEvent = (
  overrides?: Partial<EngineEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EngineEvent'} & EngineEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EngineEvent');
  return {
    __typename: 'EngineEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'a',
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'aut',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'saepe',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'unde',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'doloribus',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'aut',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'quo',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'beatae',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'minima',
  };
};

export const buildEnumConfigType = (
  overrides?: Partial<EnumConfigType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EnumConfigType'} & EnumConfigType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EnumConfigType');
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
        : [],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys') ? overrides.typeParamKeys! : [],
    values: overrides && overrides.hasOwnProperty('values') ? overrides.values! : [],
  };
};

export const buildEnumConfigValue = (
  overrides?: Partial<EnumConfigValue>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EnumConfigValue'} & EnumConfigValue => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EnumConfigValue');
  return {
    __typename: 'EnumConfigValue',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'dignissimos',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'necessitatibus',
  };
};

export const buildEnvVarConsumer = (
  overrides?: Partial<EnvVarConsumer>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EnvVarConsumer'} & EnvVarConsumer => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EnvVarConsumer');
  return {
    __typename: 'EnvVarConsumer',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'est',
    type:
      overrides && overrides.hasOwnProperty('type') ? overrides.type! : EnvVarConsumerType.RESOURCE,
  };
};

export const buildEnvVarWithConsumers = (
  overrides?: Partial<EnvVarWithConsumers>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EnvVarWithConsumers'} & EnvVarWithConsumers => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EnvVarWithConsumers');
  return {
    __typename: 'EnvVarWithConsumers',
    envVarConsumers:
      overrides && overrides.hasOwnProperty('envVarConsumers') ? overrides.envVarConsumers! : [],
    envVarName:
      overrides && overrides.hasOwnProperty('envVarName') ? overrides.envVarName! : 'quis',
  };
};

export const buildEnvVarWithConsumersList = (
  overrides?: Partial<EnvVarWithConsumersList>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EnvVarWithConsumersList'} & EnvVarWithConsumersList => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EnvVarWithConsumersList');
  return {
    __typename: 'EnvVarWithConsumersList',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildError = (
  overrides?: Partial<Error>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Error'} & Error => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Error');
  return {
    __typename: 'Error',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
  };
};

export const buildErrorChainLink = (
  overrides?: Partial<ErrorChainLink>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ErrorChainLink'} & ErrorChainLink => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ErrorChainLink');
  return {
    __typename: 'ErrorChainLink',
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    isExplicitLink:
      overrides && overrides.hasOwnProperty('isExplicitLink') ? overrides.isExplicitLink! : true,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ut',
  };
};

export const buildErrorEvent = (
  overrides?: Partial<ErrorEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ErrorEvent'} & ErrorEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ErrorEvent');
  return {
    __typename: 'ErrorEvent',
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildEvaluationStack = (
  overrides?: Partial<EvaluationStack>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EvaluationStack'} & EvaluationStack => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EvaluationStack');
  return {
    __typename: 'EvaluationStack',
    entries: overrides && overrides.hasOwnProperty('entries') ? overrides.entries! : [],
  };
};

export const buildEvaluationStackListItemEntry = (
  overrides?: Partial<EvaluationStackListItemEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EvaluationStackListItemEntry'} & EvaluationStackListItemEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EvaluationStackListItemEntry');
  return {
    __typename: 'EvaluationStackListItemEntry',
    listIndex: overrides && overrides.hasOwnProperty('listIndex') ? overrides.listIndex! : 8595,
  };
};

export const buildEvaluationStackMapKeyEntry = (
  overrides?: Partial<EvaluationStackMapKeyEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EvaluationStackMapKeyEntry'} & EvaluationStackMapKeyEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EvaluationStackMapKeyEntry');
  return {
    __typename: 'EvaluationStackMapKeyEntry',
    mapKey: overrides && overrides.hasOwnProperty('mapKey') ? overrides.mapKey! : 'qui',
  };
};

export const buildEvaluationStackMapValueEntry = (
  overrides?: Partial<EvaluationStackMapValueEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EvaluationStackMapValueEntry'} & EvaluationStackMapValueEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EvaluationStackMapValueEntry');
  return {
    __typename: 'EvaluationStackMapValueEntry',
    mapKey: overrides && overrides.hasOwnProperty('mapKey') ? overrides.mapKey! : 'architecto',
  };
};

export const buildEvaluationStackPathEntry = (
  overrides?: Partial<EvaluationStackPathEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EvaluationStackPathEntry'} & EvaluationStackPathEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EvaluationStackPathEntry');
  return {
    __typename: 'EvaluationStackPathEntry',
    fieldName: overrides && overrides.hasOwnProperty('fieldName') ? overrides.fieldName! : 'ipsa',
  };
};

export const buildEventConnection = (
  overrides?: Partial<EventConnection>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EventConnection'} & EventConnection => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EventConnection');
  return {
    __typename: 'EventConnection',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'dolor',
    events: overrides && overrides.hasOwnProperty('events') ? overrides.events! : [],
    hasMore: overrides && overrides.hasOwnProperty('hasMore') ? overrides.hasMore! : true,
  };
};

export const buildEventTag = (
  overrides?: Partial<EventTag>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'EventTag'} & EventTag => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('EventTag');
  return {
    __typename: 'EventTag',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'saepe',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'laboriosam',
  };
};

export const buildExecutionMetadata = (
  overrides?: Partial<ExecutionMetadata>,
  _relationshipsToOmit: Set<string> = new Set(),
): ExecutionMetadata => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionMetadata');
  return {
    parentRunId:
      overrides && overrides.hasOwnProperty('parentRunId') ? overrides.parentRunId! : 'autem',
    rootRunId: overrides && overrides.hasOwnProperty('rootRunId') ? overrides.rootRunId! : 'ut',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'dolor',
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildExecutionParams = (
  overrides?: Partial<ExecutionParams>,
  _relationshipsToOmit: Set<string> = new Set(),
): ExecutionParams => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionParams');
  return {
    executionMetadata:
      overrides && overrides.hasOwnProperty('executionMetadata')
        ? overrides.executionMetadata!
        : relationshipsToOmit.has('ExecutionMetadata')
        ? ({} as ExecutionMetadata)
        : buildExecutionMetadata({}, relationshipsToOmit),
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'porro',
    preset: overrides && overrides.hasOwnProperty('preset') ? overrides.preset! : 'voluptates',
    runConfigData:
      overrides && overrides.hasOwnProperty('runConfigData')
        ? overrides.runConfigData!
        : 'nesciunt',
    selector:
      overrides && overrides.hasOwnProperty('selector')
        ? overrides.selector!
        : relationshipsToOmit.has('JobOrPipelineSelector')
        ? ({} as JobOrPipelineSelector)
        : buildJobOrPipelineSelector({}, relationshipsToOmit),
    stepKeys: overrides && overrides.hasOwnProperty('stepKeys') ? overrides.stepKeys! : [],
  };
};

export const buildExecutionPlan = (
  overrides?: Partial<ExecutionPlan>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionPlan'} & ExecutionPlan => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionPlan');
  return {
    __typename: 'ExecutionPlan',
    artifactsPersisted:
      overrides && overrides.hasOwnProperty('artifactsPersisted')
        ? overrides.artifactsPersisted!
        : true,
    steps: overrides && overrides.hasOwnProperty('steps') ? overrides.steps! : [],
  };
};

export const buildExecutionStep = (
  overrides?: Partial<ExecutionStep>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStep'} & ExecutionStep => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStep');
  return {
    __typename: 'ExecutionStep',
    inputs: overrides && overrides.hasOwnProperty('inputs') ? overrides.inputs! : [],
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'ut',
    kind: overrides && overrides.hasOwnProperty('kind') ? overrides.kind! : StepKind.COMPUTE,
    metadata: overrides && overrides.hasOwnProperty('metadata') ? overrides.metadata! : [],
    outputs: overrides && overrides.hasOwnProperty('outputs') ? overrides.outputs! : [],
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'aspernatur',
  };
};

export const buildExecutionStepFailureEvent = (
  overrides?: Partial<ExecutionStepFailureEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepFailureEvent'} & ExecutionStepFailureEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepFailureEvent');
  return {
    __typename: 'ExecutionStepFailureEvent',
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    errorSource:
      overrides && overrides.hasOwnProperty('errorSource')
        ? overrides.errorSource!
        : ErrorSource.FRAMEWORK_ERROR,
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    failureMetadata:
      overrides && overrides.hasOwnProperty('failureMetadata')
        ? overrides.failureMetadata!
        : relationshipsToOmit.has('FailureMetadata')
        ? ({} as FailureMetadata)
        : buildFailureMetadata({}, relationshipsToOmit),
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<ExecutionStepInput>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepInput'} & ExecutionStepInput => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepInput');
  return {
    __typename: 'ExecutionStepInput',
    dependsOn: overrides && overrides.hasOwnProperty('dependsOn') ? overrides.dependsOn! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'tempore',
  };
};

export const buildExecutionStepInputEvent = (
  overrides?: Partial<ExecutionStepInputEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepInputEvent'} & ExecutionStepInputEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepInputEvent');
  return {
    __typename: 'ExecutionStepInputEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    inputName:
      overrides && overrides.hasOwnProperty('inputName') ? overrides.inputName! : 'inventore',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'dolore',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'sit',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'animi',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'dolores',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'dolor',
    typeCheck:
      overrides && overrides.hasOwnProperty('typeCheck')
        ? overrides.typeCheck!
        : relationshipsToOmit.has('TypeCheck')
        ? ({} as TypeCheck)
        : buildTypeCheck({}, relationshipsToOmit),
  };
};

export const buildExecutionStepOutput = (
  overrides?: Partial<ExecutionStepOutput>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepOutput'} & ExecutionStepOutput => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepOutput');
  return {
    __typename: 'ExecutionStepOutput',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'rerum',
  };
};

export const buildExecutionStepOutputEvent = (
  overrides?: Partial<ExecutionStepOutputEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepOutputEvent'} & ExecutionStepOutputEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepOutputEvent');
  return {
    __typename: 'ExecutionStepOutputEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'vel',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'quae',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quo',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    outputName:
      overrides && overrides.hasOwnProperty('outputName') ? overrides.outputName! : 'animi',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'repellat',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'sed',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'sed',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'ducimus',
    typeCheck:
      overrides && overrides.hasOwnProperty('typeCheck')
        ? overrides.typeCheck!
        : relationshipsToOmit.has('TypeCheck')
        ? ({} as TypeCheck)
        : buildTypeCheck({}, relationshipsToOmit),
  };
};

export const buildExecutionStepRestartEvent = (
  overrides?: Partial<ExecutionStepRestartEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepRestartEvent'} & ExecutionStepRestartEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepRestartEvent');
  return {
    __typename: 'ExecutionStepRestartEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<ExecutionStepSkippedEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepSkippedEvent'} & ExecutionStepSkippedEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepSkippedEvent');
  return {
    __typename: 'ExecutionStepSkippedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<ExecutionStepStartEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepStartEvent'} & ExecutionStepStartEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepStartEvent');
  return {
    __typename: 'ExecutionStepStartEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<ExecutionStepSuccessEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepSuccessEvent'} & ExecutionStepSuccessEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepSuccessEvent');
  return {
    __typename: 'ExecutionStepSuccessEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<ExecutionStepUpForRetryEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExecutionStepUpForRetryEvent'} & ExecutionStepUpForRetryEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionStepUpForRetryEvent');
  return {
    __typename: 'ExecutionStepUpForRetryEvent',
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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

export const buildExecutionTag = (
  overrides?: Partial<ExecutionTag>,
  _relationshipsToOmit: Set<string> = new Set(),
): ExecutionTag => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExecutionTag');
  return {
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'quis',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'aut',
  };
};

export const buildExpectationResult = (
  overrides?: Partial<ExpectationResult>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ExpectationResult'} & ExpectationResult => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ExpectationResult');
  return {
    __typename: 'ExpectationResult',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'dignissimos',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'molestiae',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    success: overrides && overrides.hasOwnProperty('success') ? overrides.success! : false,
  };
};

export const buildFailureMetadata = (
  overrides?: Partial<FailureMetadata>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'FailureMetadata'} & FailureMetadata => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('FailureMetadata');
  return {
    __typename: 'FailureMetadata',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'ex',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'unde',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
  };
};

export const buildFieldNotDefinedConfigError = (
  overrides?: Partial<FieldNotDefinedConfigError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'FieldNotDefinedConfigError'} & FieldNotDefinedConfigError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('FieldNotDefinedConfigError');
  return {
    __typename: 'FieldNotDefinedConfigError',
    fieldName:
      overrides && overrides.hasOwnProperty('fieldName') ? overrides.fieldName! : 'voluptatem',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ut',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : [],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : EvaluationErrorReason.FIELDS_NOT_DEFINED,
    stack:
      overrides && overrides.hasOwnProperty('stack')
        ? overrides.stack!
        : relationshipsToOmit.has('EvaluationStack')
        ? ({} as EvaluationStack)
        : buildEvaluationStack({}, relationshipsToOmit),
  };
};

export const buildFieldsNotDefinedConfigError = (
  overrides?: Partial<FieldsNotDefinedConfigError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'FieldsNotDefinedConfigError'} & FieldsNotDefinedConfigError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('FieldsNotDefinedConfigError');
  return {
    __typename: 'FieldsNotDefinedConfigError',
    fieldNames: overrides && overrides.hasOwnProperty('fieldNames') ? overrides.fieldNames! : [],
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'dolore',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : [],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : EvaluationErrorReason.FIELDS_NOT_DEFINED,
    stack:
      overrides && overrides.hasOwnProperty('stack')
        ? overrides.stack!
        : relationshipsToOmit.has('EvaluationStack')
        ? ({} as EvaluationStack)
        : buildEvaluationStack({}, relationshipsToOmit),
  };
};

export const buildFloatMetadataEntry = (
  overrides?: Partial<FloatMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'FloatMetadataEntry'} & FloatMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('FloatMetadataEntry');
  return {
    __typename: 'FloatMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'iusto',
    floatValue: overrides && overrides.hasOwnProperty('floatValue') ? overrides.floatValue! : 5.68,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'velit',
  };
};

export const buildFreshnessAutoMaterializeCondition = (
  overrides?: Partial<FreshnessAutoMaterializeCondition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'FreshnessAutoMaterializeCondition'} & FreshnessAutoMaterializeCondition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('FreshnessAutoMaterializeCondition');
  return {
    __typename: 'FreshnessAutoMaterializeCondition',
    decisionType:
      overrides && overrides.hasOwnProperty('decisionType')
        ? overrides.decisionType!
        : AutoMaterializeDecisionType.DISCARD,
    partitionKeysOrError:
      overrides && overrides.hasOwnProperty('partitionKeysOrError')
        ? overrides.partitionKeysOrError!
        : relationshipsToOmit.has('PartitionKeys')
        ? ({} as PartitionKeys)
        : buildPartitionKeys({}, relationshipsToOmit),
  };
};

export const buildFreshnessPolicy = (
  overrides?: Partial<FreshnessPolicy>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'FreshnessPolicy'} & FreshnessPolicy => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('FreshnessPolicy');
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
  overrides?: Partial<Graph>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Graph'} & Graph => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Graph');
  return {
    __typename: 'Graph',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'aspernatur',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '000b66d3-d51f-4db4-9757-da36cd59fc26',
    modes: overrides && overrides.hasOwnProperty('modes') ? overrides.modes! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'quidem',
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : relationshipsToOmit.has('SolidHandle')
        ? ({} as SolidHandle)
        : buildSolidHandle({}, relationshipsToOmit),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles') ? overrides.solidHandles! : [],
    solids: overrides && overrides.hasOwnProperty('solids') ? overrides.solids! : [],
  };
};

export const buildGraphNotFoundError = (
  overrides?: Partial<GraphNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'GraphNotFoundError'} & GraphNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('GraphNotFoundError');
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
  overrides?: Partial<GraphSelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): GraphSelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('GraphSelector');
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
  overrides?: Partial<HandledOutputEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'HandledOutputEvent'} & HandledOutputEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('HandledOutputEvent');
  return {
    __typename: 'HandledOutputEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quibusdam',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'ducimus',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    managerKey:
      overrides && overrides.hasOwnProperty('managerKey') ? overrides.managerKey! : 'ipsa',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'id',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
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
  overrides?: Partial<HookCompletedEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'HookCompletedEvent'} & HookCompletedEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('HookCompletedEvent');
  return {
    __typename: 'HookCompletedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'aspernatur',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'iusto',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'labore',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'atque',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'qui',
  };
};

export const buildHookErroredEvent = (
  overrides?: Partial<HookErroredEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'HookErroredEvent'} & HookErroredEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('HookErroredEvent');
  return {
    __typename: 'HookErroredEvent',
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'molestias',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'voluptate',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'labore',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'possimus',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'qui',
  };
};

export const buildHookSkippedEvent = (
  overrides?: Partial<HookSkippedEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'HookSkippedEvent'} & HookSkippedEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('HookSkippedEvent');
  return {
    __typename: 'HookSkippedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'id',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'iste',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'quia',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'aperiam',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'eaque',
  };
};

export const buildIPipelineSnapshot = (
  overrides?: Partial<IPipelineSnapshot>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'IPipelineSnapshot'} & IPipelineSnapshot => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('IPipelineSnapshot');
  return {
    __typename: 'IPipelineSnapshot',
    dagsterTypeOrError:
      overrides && overrides.hasOwnProperty('dagsterTypeOrError')
        ? overrides.dagsterTypeOrError!
        : relationshipsToOmit.has('DagsterTypeNotFoundError')
        ? ({} as DagsterTypeNotFoundError)
        : buildDagsterTypeNotFoundError({}, relationshipsToOmit),
    dagsterTypes:
      overrides && overrides.hasOwnProperty('dagsterTypes') ? overrides.dagsterTypes! : [],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'velit',
    graphName:
      overrides && overrides.hasOwnProperty('graphName') ? overrides.graphName! : 'aperiam',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    modes: overrides && overrides.hasOwnProperty('modes') ? overrides.modes! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'autem',
    parentSnapshotId:
      overrides && overrides.hasOwnProperty('parentSnapshotId')
        ? overrides.parentSnapshotId!
        : 'deserunt',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'quo',
    runs: overrides && overrides.hasOwnProperty('runs') ? overrides.runs! : [],
    schedules: overrides && overrides.hasOwnProperty('schedules') ? overrides.schedules! : [],
    sensors: overrides && overrides.hasOwnProperty('sensors') ? overrides.sensors! : [],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : relationshipsToOmit.has('SolidHandle')
        ? ({} as SolidHandle)
        : buildSolidHandle({}, relationshipsToOmit),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles') ? overrides.solidHandles! : [],
    solids: overrides && overrides.hasOwnProperty('solids') ? overrides.solids! : [],
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildISolidDefinition = (
  overrides?: Partial<ISolidDefinition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ISolidDefinition'} & ISolidDefinition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ISolidDefinition');
  return {
    __typename: 'ISolidDefinition',
    assetNodes: overrides && overrides.hasOwnProperty('assetNodes') ? overrides.assetNodes! : [],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'et',
    inputDefinitions:
      overrides && overrides.hasOwnProperty('inputDefinitions') ? overrides.inputDefinitions! : [],
    metadata: overrides && overrides.hasOwnProperty('metadata') ? overrides.metadata! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'iure',
    outputDefinitions:
      overrides && overrides.hasOwnProperty('outputDefinitions')
        ? overrides.outputDefinitions!
        : [],
  };
};

export const buildInput = (
  overrides?: Partial<Input>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Input'} & Input => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Input');
  return {
    __typename: 'Input',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : relationshipsToOmit.has('InputDefinition')
        ? ({} as InputDefinition)
        : buildInputDefinition({}, relationshipsToOmit),
    dependsOn: overrides && overrides.hasOwnProperty('dependsOn') ? overrides.dependsOn! : [],
    isDynamicCollect:
      overrides && overrides.hasOwnProperty('isDynamicCollect')
        ? overrides.isDynamicCollect!
        : false,
    solid:
      overrides && overrides.hasOwnProperty('solid')
        ? overrides.solid!
        : relationshipsToOmit.has('Solid')
        ? ({} as Solid)
        : buildSolid({}, relationshipsToOmit),
  };
};

export const buildInputDefinition = (
  overrides?: Partial<InputDefinition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InputDefinition'} & InputDefinition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InputDefinition');
  return {
    __typename: 'InputDefinition',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'iusto',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'non',
    solidDefinition:
      overrides && overrides.hasOwnProperty('solidDefinition')
        ? overrides.solidDefinition!
        : relationshipsToOmit.has('SolidDefinition')
        ? ({} as SolidDefinition)
        : buildSolidDefinition({}, relationshipsToOmit),
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : relationshipsToOmit.has('DagsterType')
        ? ({} as DagsterType)
        : buildDagsterType({}, relationshipsToOmit),
  };
};

export const buildInputMapping = (
  overrides?: Partial<InputMapping>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InputMapping'} & InputMapping => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InputMapping');
  return {
    __typename: 'InputMapping',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : relationshipsToOmit.has('InputDefinition')
        ? ({} as InputDefinition)
        : buildInputDefinition({}, relationshipsToOmit),
    mappedInput:
      overrides && overrides.hasOwnProperty('mappedInput')
        ? overrides.mappedInput!
        : relationshipsToOmit.has('Input')
        ? ({} as Input)
        : buildInput({}, relationshipsToOmit),
  };
};

export const buildInputTag = (
  overrides?: Partial<InputTag>,
  _relationshipsToOmit: Set<string> = new Set(),
): InputTag => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InputTag');
  return {
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'possimus',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'quod',
  };
};

export const buildInstance = (
  overrides?: Partial<Instance>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Instance'} & Instance => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Instance');
  return {
    __typename: 'Instance',
    autoMaterializePaused:
      overrides && overrides.hasOwnProperty('autoMaterializePaused')
        ? overrides.autoMaterializePaused!
        : true,
    concurrencyLimits:
      overrides && overrides.hasOwnProperty('concurrencyLimits')
        ? overrides.concurrencyLimits!
        : [],
    daemonHealth:
      overrides && overrides.hasOwnProperty('daemonHealth')
        ? overrides.daemonHealth!
        : relationshipsToOmit.has('DaemonHealth')
        ? ({} as DaemonHealth)
        : buildDaemonHealth({}, relationshipsToOmit),
    executablePath:
      overrides && overrides.hasOwnProperty('executablePath') ? overrides.executablePath! : 'fuga',
    hasCapturedLogManager:
      overrides && overrides.hasOwnProperty('hasCapturedLogManager')
        ? overrides.hasCapturedLogManager!
        : true,
    hasInfo: overrides && overrides.hasOwnProperty('hasInfo') ? overrides.hasInfo! : true,
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'deleniti',
    info: overrides && overrides.hasOwnProperty('info') ? overrides.info! : 'qui',
    runLauncher:
      overrides && overrides.hasOwnProperty('runLauncher')
        ? overrides.runLauncher!
        : relationshipsToOmit.has('RunLauncher')
        ? ({} as RunLauncher)
        : buildRunLauncher({}, relationshipsToOmit),
    runQueuingSupported:
      overrides && overrides.hasOwnProperty('runQueuingSupported')
        ? overrides.runQueuingSupported!
        : true,
  };
};

export const buildInstigationEvent = (
  overrides?: Partial<InstigationEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InstigationEvent'} & InstigationEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InstigationEvent');
  return {
    __typename: 'InstigationEvent',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ea',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'architecto',
  };
};

export const buildInstigationEventConnection = (
  overrides?: Partial<InstigationEventConnection>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InstigationEventConnection'} & InstigationEventConnection => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InstigationEventConnection');
  return {
    __typename: 'InstigationEventConnection',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'harum',
    events: overrides && overrides.hasOwnProperty('events') ? overrides.events! : [],
    hasMore: overrides && overrides.hasOwnProperty('hasMore') ? overrides.hasMore! : true,
  };
};

export const buildInstigationSelector = (
  overrides?: Partial<InstigationSelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): InstigationSelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InstigationSelector');
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
  overrides?: Partial<InstigationState>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InstigationState'} & InstigationState => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InstigationState');
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
        : InstigationType.SCHEDULE,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'praesentium',
    nextTick:
      overrides && overrides.hasOwnProperty('nextTick')
        ? overrides.nextTick!
        : relationshipsToOmit.has('DryRunInstigationTick')
        ? ({} as DryRunInstigationTick)
        : buildDryRunInstigationTick({}, relationshipsToOmit),
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'omnis',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'non',
    repositoryOrigin:
      overrides && overrides.hasOwnProperty('repositoryOrigin')
        ? overrides.repositoryOrigin!
        : relationshipsToOmit.has('RepositoryOrigin')
        ? ({} as RepositoryOrigin)
        : buildRepositoryOrigin({}, relationshipsToOmit),
    runningCount:
      overrides && overrides.hasOwnProperty('runningCount') ? overrides.runningCount! : 6523,
    runs: overrides && overrides.hasOwnProperty('runs') ? overrides.runs! : [],
    runsCount: overrides && overrides.hasOwnProperty('runsCount') ? overrides.runsCount! : 6663,
    selectorId: overrides && overrides.hasOwnProperty('selectorId') ? overrides.selectorId! : 'aut',
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : InstigationStatus.RUNNING,
    tick:
      overrides && overrides.hasOwnProperty('tick')
        ? overrides.tick!
        : relationshipsToOmit.has('InstigationTick')
        ? ({} as InstigationTick)
        : buildInstigationTick({}, relationshipsToOmit),
    ticks: overrides && overrides.hasOwnProperty('ticks') ? overrides.ticks! : [],
    typeSpecificData:
      overrides && overrides.hasOwnProperty('typeSpecificData')
        ? overrides.typeSpecificData!
        : relationshipsToOmit.has('ScheduleData')
        ? ({} as ScheduleData)
        : buildScheduleData({}, relationshipsToOmit),
  };
};

export const buildInstigationStateNotFoundError = (
  overrides?: Partial<InstigationStateNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InstigationStateNotFoundError'} & InstigationStateNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InstigationStateNotFoundError');
  return {
    __typename: 'InstigationStateNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'nihil',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'fuga',
  };
};

export const buildInstigationStates = (
  overrides?: Partial<InstigationStates>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InstigationStates'} & InstigationStates => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InstigationStates');
  return {
    __typename: 'InstigationStates',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildInstigationTick = (
  overrides?: Partial<InstigationTick>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InstigationTick'} & InstigationTick => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InstigationTick');
  return {
    __typename: 'InstigationTick',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'voluptatem',
    dynamicPartitionsRequestResults:
      overrides && overrides.hasOwnProperty('dynamicPartitionsRequestResults')
        ? overrides.dynamicPartitionsRequestResults!
        : [],
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'd7be0ce0-364e-498b-98ec-cc8b0f746723',
    logEvents:
      overrides && overrides.hasOwnProperty('logEvents')
        ? overrides.logEvents!
        : relationshipsToOmit.has('InstigationEventConnection')
        ? ({} as InstigationEventConnection)
        : buildInstigationEventConnection({}, relationshipsToOmit),
    logKey: overrides && overrides.hasOwnProperty('logKey') ? overrides.logKey! : [],
    originRunIds:
      overrides && overrides.hasOwnProperty('originRunIds') ? overrides.originRunIds! : [],
    runIds: overrides && overrides.hasOwnProperty('runIds') ? overrides.runIds! : [],
    runKeys: overrides && overrides.hasOwnProperty('runKeys') ? overrides.runKeys! : [],
    runs: overrides && overrides.hasOwnProperty('runs') ? overrides.runs! : [],
    skipReason:
      overrides && overrides.hasOwnProperty('skipReason') ? overrides.skipReason! : 'maxime',
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : InstigationTickStatus.FAILURE,
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 6.06,
  };
};

export const buildIntMetadataEntry = (
  overrides?: Partial<IntMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'IntMetadataEntry'} & IntMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('IntMetadataEntry');
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
  overrides?: Partial<InvalidOutputError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InvalidOutputError'} & InvalidOutputError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InvalidOutputError');
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
  overrides?: Partial<InvalidPipelineRunsFilterError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InvalidPipelineRunsFilterError'} & InvalidPipelineRunsFilterError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InvalidPipelineRunsFilterError');
  return {
    __typename: 'InvalidPipelineRunsFilterError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
  };
};

export const buildInvalidStepError = (
  overrides?: Partial<InvalidStepError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InvalidStepError'} & InvalidStepError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InvalidStepError');
  return {
    __typename: 'InvalidStepError',
    invalidStepKey:
      overrides && overrides.hasOwnProperty('invalidStepKey')
        ? overrides.invalidStepKey!
        : 'doloribus',
  };
};

export const buildInvalidSubsetError = (
  overrides?: Partial<InvalidSubsetError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'InvalidSubsetError'} & InvalidSubsetError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('InvalidSubsetError');
  return {
    __typename: 'InvalidSubsetError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'aut',
    pipeline:
      overrides && overrides.hasOwnProperty('pipeline')
        ? overrides.pipeline!
        : relationshipsToOmit.has('Pipeline')
        ? ({} as Pipeline)
        : buildPipeline({}, relationshipsToOmit),
  };
};

export const buildJob = (
  overrides?: Partial<Job>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Job'} & Job => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Job');
  return {
    __typename: 'Job',
    dagsterTypeOrError:
      overrides && overrides.hasOwnProperty('dagsterTypeOrError')
        ? overrides.dagsterTypeOrError!
        : relationshipsToOmit.has('DagsterTypeNotFoundError')
        ? ({} as DagsterTypeNotFoundError)
        : buildDagsterTypeNotFoundError({}, relationshipsToOmit),
    dagsterTypes:
      overrides && overrides.hasOwnProperty('dagsterTypes') ? overrides.dagsterTypes! : [],
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
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    modes: overrides && overrides.hasOwnProperty('modes') ? overrides.modes! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'rerum',
    parentSnapshotId:
      overrides && overrides.hasOwnProperty('parentSnapshotId')
        ? overrides.parentSnapshotId!
        : 'tempore',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'maxime',
    presets: overrides && overrides.hasOwnProperty('presets') ? overrides.presets! : [],
    repository:
      overrides && overrides.hasOwnProperty('repository')
        ? overrides.repository!
        : relationshipsToOmit.has('Repository')
        ? ({} as Repository)
        : buildRepository({}, relationshipsToOmit),
    runs: overrides && overrides.hasOwnProperty('runs') ? overrides.runs! : [],
    schedules: overrides && overrides.hasOwnProperty('schedules') ? overrides.schedules! : [],
    sensors: overrides && overrides.hasOwnProperty('sensors') ? overrides.sensors! : [],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : relationshipsToOmit.has('SolidHandle')
        ? ({} as SolidHandle)
        : buildSolidHandle({}, relationshipsToOmit),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles') ? overrides.solidHandles! : [],
    solids: overrides && overrides.hasOwnProperty('solids') ? overrides.solids! : [],
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildJobOrPipelineSelector = (
  overrides?: Partial<JobOrPipelineSelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): JobOrPipelineSelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('JobOrPipelineSelector');
  return {
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection') ? overrides.assetSelection! : [],
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
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
  };
};

export const buildJobWithOps = (
  overrides?: Partial<JobWithOps>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'JobWithOps'} & JobWithOps => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('JobWithOps');
  return {
    __typename: 'JobWithOps',
    job:
      overrides && overrides.hasOwnProperty('job')
        ? overrides.job!
        : relationshipsToOmit.has('Job')
        ? ({} as Job)
        : buildJob({}, relationshipsToOmit),
    opsUsing: overrides && overrides.hasOwnProperty('opsUsing') ? overrides.opsUsing! : [],
  };
};

export const buildJsonMetadataEntry = (
  overrides?: Partial<JsonMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'JsonMetadataEntry'} & JsonMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('JsonMetadataEntry');
  return {
    __typename: 'JsonMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'et',
    jsonString: overrides && overrides.hasOwnProperty('jsonString') ? overrides.jsonString! : 'qui',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'ut',
  };
};

export const buildLaunchBackfillMutation = (
  overrides?: Partial<LaunchBackfillMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LaunchBackfillMutation'} & LaunchBackfillMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LaunchBackfillMutation');
  return {
    __typename: 'LaunchBackfillMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('ConflictingExecutionParamsError')
        ? ({} as ConflictingExecutionParamsError)
        : buildConflictingExecutionParamsError({}, relationshipsToOmit),
  };
};

export const buildLaunchBackfillParams = (
  overrides?: Partial<LaunchBackfillParams>,
  _relationshipsToOmit: Set<string> = new Set(),
): LaunchBackfillParams => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LaunchBackfillParams');
  return {
    allPartitions:
      overrides && overrides.hasOwnProperty('allPartitions') ? overrides.allPartitions! : false,
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection') ? overrides.assetSelection! : [],
    forceSynchronousSubmission:
      overrides && overrides.hasOwnProperty('forceSynchronousSubmission')
        ? overrides.forceSynchronousSubmission!
        : true,
    fromFailure:
      overrides && overrides.hasOwnProperty('fromFailure') ? overrides.fromFailure! : true,
    partitionNames:
      overrides && overrides.hasOwnProperty('partitionNames') ? overrides.partitionNames! : [],
    reexecutionSteps:
      overrides && overrides.hasOwnProperty('reexecutionSteps') ? overrides.reexecutionSteps! : [],
    selector:
      overrides && overrides.hasOwnProperty('selector')
        ? overrides.selector!
        : relationshipsToOmit.has('PartitionSetSelector')
        ? ({} as PartitionSetSelector)
        : buildPartitionSetSelector({}, relationshipsToOmit),
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildLaunchBackfillSuccess = (
  overrides?: Partial<LaunchBackfillSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LaunchBackfillSuccess'} & LaunchBackfillSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LaunchBackfillSuccess');
  return {
    __typename: 'LaunchBackfillSuccess',
    backfillId: overrides && overrides.hasOwnProperty('backfillId') ? overrides.backfillId! : 'sit',
    launchedRunIds:
      overrides && overrides.hasOwnProperty('launchedRunIds') ? overrides.launchedRunIds! : [],
  };
};

export const buildLaunchPipelineRunSuccess = (
  overrides?: Partial<LaunchPipelineRunSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LaunchPipelineRunSuccess'} & LaunchPipelineRunSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LaunchPipelineRunSuccess');
  return {
    __typename: 'LaunchPipelineRunSuccess',
    run:
      overrides && overrides.hasOwnProperty('run')
        ? overrides.run!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
  };
};

export const buildLaunchRunMutation = (
  overrides?: Partial<LaunchRunMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LaunchRunMutation'} & LaunchRunMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LaunchRunMutation');
  return {
    __typename: 'LaunchRunMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('ConflictingExecutionParamsError')
        ? ({} as ConflictingExecutionParamsError)
        : buildConflictingExecutionParamsError({}, relationshipsToOmit),
  };
};

export const buildLaunchRunReexecutionMutation = (
  overrides?: Partial<LaunchRunReexecutionMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LaunchRunReexecutionMutation'} & LaunchRunReexecutionMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LaunchRunReexecutionMutation');
  return {
    __typename: 'LaunchRunReexecutionMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('ConflictingExecutionParamsError')
        ? ({} as ConflictingExecutionParamsError)
        : buildConflictingExecutionParamsError({}, relationshipsToOmit),
  };
};

export const buildLaunchRunSuccess = (
  overrides?: Partial<LaunchRunSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LaunchRunSuccess'} & LaunchRunSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LaunchRunSuccess');
  return {
    __typename: 'LaunchRunSuccess',
    run:
      overrides && overrides.hasOwnProperty('run')
        ? overrides.run!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
  };
};

export const buildListDagsterType = (
  overrides?: Partial<ListDagsterType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ListDagsterType'} & ListDagsterType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ListDagsterType');
  return {
    __typename: 'ListDagsterType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'enim',
    displayName:
      overrides && overrides.hasOwnProperty('displayName') ? overrides.displayName! : 'soluta',
    innerTypes: overrides && overrides.hasOwnProperty('innerTypes') ? overrides.innerTypes! : [],
    inputSchemaType:
      overrides && overrides.hasOwnProperty('inputSchemaType')
        ? overrides.inputSchemaType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    isBuiltin: overrides && overrides.hasOwnProperty('isBuiltin') ? overrides.isBuiltin! : true,
    isList: overrides && overrides.hasOwnProperty('isList') ? overrides.isList! : true,
    isNothing: overrides && overrides.hasOwnProperty('isNothing') ? overrides.isNothing! : true,
    isNullable: overrides && overrides.hasOwnProperty('isNullable') ? overrides.isNullable! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'aut',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'culpa',
    ofType:
      overrides && overrides.hasOwnProperty('ofType')
        ? overrides.ofType!
        : relationshipsToOmit.has('DagsterType')
        ? ({} as DagsterType)
        : buildDagsterType({}, relationshipsToOmit),
    outputSchemaType:
      overrides && overrides.hasOwnProperty('outputSchemaType')
        ? overrides.outputSchemaType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
  };
};

export const buildLoadedInputEvent = (
  overrides?: Partial<LoadedInputEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LoadedInputEvent'} & LoadedInputEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LoadedInputEvent');
  return {
    __typename: 'LoadedInputEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'impedit',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    inputName: overrides && overrides.hasOwnProperty('inputName') ? overrides.inputName! : 'quia',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'facere',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    managerKey:
      overrides && overrides.hasOwnProperty('managerKey') ? overrides.managerKey! : 'quae',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'eveniet',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
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
  overrides?: Partial<LocationStateChangeEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LocationStateChangeEvent'} & LocationStateChangeEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LocationStateChangeEvent');
  return {
    __typename: 'LocationStateChangeEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : LocationStateChangeEventType.LOCATION_DISCONNECTED,
    locationName:
      overrides && overrides.hasOwnProperty('locationName') ? overrides.locationName! : 'tempora',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'at',
    serverId: overrides && overrides.hasOwnProperty('serverId') ? overrides.serverId! : 'adipisci',
  };
};

export const buildLocationStateChangeSubscription = (
  overrides?: Partial<LocationStateChangeSubscription>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LocationStateChangeSubscription'} & LocationStateChangeSubscription => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LocationStateChangeSubscription');
  return {
    __typename: 'LocationStateChangeSubscription',
    event:
      overrides && overrides.hasOwnProperty('event')
        ? overrides.event!
        : relationshipsToOmit.has('LocationStateChangeEvent')
        ? ({} as LocationStateChangeEvent)
        : buildLocationStateChangeEvent({}, relationshipsToOmit),
  };
};

export const buildLogMessageEvent = (
  overrides?: Partial<LogMessageEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LogMessageEvent'} & LogMessageEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LogMessageEvent');
  return {
    __typename: 'LogMessageEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<LogTelemetrySuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LogTelemetrySuccess'} & LogTelemetrySuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LogTelemetrySuccess');
  return {
    __typename: 'LogTelemetrySuccess',
    action: overrides && overrides.hasOwnProperty('action') ? overrides.action! : 'assumenda',
  };
};

export const buildLogger = (
  overrides?: Partial<Logger>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Logger'} & Logger => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Logger');
  return {
    __typename: 'Logger',
    configField:
      overrides && overrides.hasOwnProperty('configField')
        ? overrides.configField!
        : relationshipsToOmit.has('ConfigTypeField')
        ? ({} as ConfigTypeField)
        : buildConfigTypeField({}, relationshipsToOmit),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'non',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'quas',
  };
};

export const buildLogsCapturedEvent = (
  overrides?: Partial<LogsCapturedEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'LogsCapturedEvent'} & LogsCapturedEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('LogsCapturedEvent');
  return {
    __typename: 'LogsCapturedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    externalStderrUrl:
      overrides && overrides.hasOwnProperty('externalStderrUrl')
        ? overrides.externalStderrUrl!
        : 'velit',
    externalStdoutUrl:
      overrides && overrides.hasOwnProperty('externalStdoutUrl')
        ? overrides.externalStdoutUrl!
        : 'consequatur',
    externalUrl:
      overrides && overrides.hasOwnProperty('externalUrl') ? overrides.externalUrl! : 'qui',
    fileKey: overrides && overrides.hasOwnProperty('fileKey') ? overrides.fileKey! : 'et',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    logKey: overrides && overrides.hasOwnProperty('logKey') ? overrides.logKey! : 'fuga',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ex',
    pid: overrides && overrides.hasOwnProperty('pid') ? overrides.pid! : 7623,
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'modi',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'assumenda',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'quia',
    stepKeys: overrides && overrides.hasOwnProperty('stepKeys') ? overrides.stepKeys! : [],
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'et',
  };
};

export const buildMapConfigType = (
  overrides?: Partial<MapConfigType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MapConfigType'} & MapConfigType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MapConfigType');
  return {
    __typename: 'MapConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quis',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'temporibus',
    keyLabelName:
      overrides && overrides.hasOwnProperty('keyLabelName') ? overrides.keyLabelName! : 'nostrum',
    keyType:
      overrides && overrides.hasOwnProperty('keyType')
        ? overrides.keyType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys') ? overrides.typeParamKeys! : [],
    valueType:
      overrides && overrides.hasOwnProperty('valueType')
        ? overrides.valueType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
  };
};

export const buildMarkdownMetadataEntry = (
  overrides?: Partial<MarkdownMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MarkdownMetadataEntry'} & MarkdownMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MarkdownMetadataEntry');
  return {
    __typename: 'MarkdownMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'eum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'nam',
    mdStr: overrides && overrides.hasOwnProperty('mdStr') ? overrides.mdStr! : 'quia',
  };
};

export const buildMarkerEvent = (
  overrides?: Partial<MarkerEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MarkerEvent'} & MarkerEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MarkerEvent');
  return {
    __typename: 'MarkerEvent',
    markerEnd:
      overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'voluptas',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'ut',
  };
};

export const buildMarshalledInput = (
  overrides?: Partial<MarshalledInput>,
  _relationshipsToOmit: Set<string> = new Set(),
): MarshalledInput => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MarshalledInput');
  return {
    inputName: overrides && overrides.hasOwnProperty('inputName') ? overrides.inputName! : 'nobis',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'nam',
  };
};

export const buildMarshalledOutput = (
  overrides?: Partial<MarshalledOutput>,
  _relationshipsToOmit: Set<string> = new Set(),
): MarshalledOutput => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MarshalledOutput');
  return {
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'sed',
    outputName:
      overrides && overrides.hasOwnProperty('outputName') ? overrides.outputName! : 'inventore',
  };
};

export const buildMaterializationEvent = (
  overrides?: Partial<MaterializationEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MaterializationEvent'} & MaterializationEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MaterializationEvent');
  return {
    __typename: 'MaterializationEvent',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    assetLineage:
      overrides && overrides.hasOwnProperty('assetLineage') ? overrides.assetLineage! : [],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'eaque',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'possimus',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'voluptatem',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    partition: overrides && overrides.hasOwnProperty('partition') ? overrides.partition! : 'velit',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'velit',
    runOrError:
      overrides && overrides.hasOwnProperty('runOrError')
        ? overrides.runOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'qui',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'ratione',
    stepStats:
      overrides && overrides.hasOwnProperty('stepStats')
        ? overrides.stepStats!
        : relationshipsToOmit.has('RunStepStats')
        ? ({} as RunStepStats)
        : buildRunStepStats({}, relationshipsToOmit),
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'id',
  };
};

export const buildMaterializationUpstreamDataVersion = (
  overrides?: Partial<MaterializationUpstreamDataVersion>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MaterializationUpstreamDataVersion'} & MaterializationUpstreamDataVersion => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MaterializationUpstreamDataVersion');
  return {
    __typename: 'MaterializationUpstreamDataVersion',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    downstreamAssetKey:
      overrides && overrides.hasOwnProperty('downstreamAssetKey')
        ? overrides.downstreamAssetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'aut',
  };
};

export const buildMaterializedPartitionRangeStatuses2D = (
  overrides?: Partial<MaterializedPartitionRangeStatuses2D>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MaterializedPartitionRangeStatuses2D'} & MaterializedPartitionRangeStatuses2D => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MaterializedPartitionRangeStatuses2D');
  return {
    __typename: 'MaterializedPartitionRangeStatuses2D',
    primaryDimEndKey:
      overrides && overrides.hasOwnProperty('primaryDimEndKey')
        ? overrides.primaryDimEndKey!
        : 'illo',
    primaryDimEndTime:
      overrides && overrides.hasOwnProperty('primaryDimEndTime')
        ? overrides.primaryDimEndTime!
        : 5.77,
    primaryDimStartKey:
      overrides && overrides.hasOwnProperty('primaryDimStartKey')
        ? overrides.primaryDimStartKey!
        : 'voluptatem',
    primaryDimStartTime:
      overrides && overrides.hasOwnProperty('primaryDimStartTime')
        ? overrides.primaryDimStartTime!
        : 3.18,
    secondaryDim:
      overrides && overrides.hasOwnProperty('secondaryDim')
        ? overrides.secondaryDim!
        : relationshipsToOmit.has('DefaultPartitionStatuses')
        ? ({} as DefaultPartitionStatuses)
        : buildDefaultPartitionStatuses({}, relationshipsToOmit),
  };
};

export const buildMaxMaterializationsExceededAutoMaterializeCondition = (
  overrides?: Partial<MaxMaterializationsExceededAutoMaterializeCondition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {
  __typename: 'MaxMaterializationsExceededAutoMaterializeCondition';
} & MaxMaterializationsExceededAutoMaterializeCondition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MaxMaterializationsExceededAutoMaterializeCondition');
  return {
    __typename: 'MaxMaterializationsExceededAutoMaterializeCondition',
    decisionType:
      overrides && overrides.hasOwnProperty('decisionType')
        ? overrides.decisionType!
        : AutoMaterializeDecisionType.DISCARD,
    partitionKeysOrError:
      overrides && overrides.hasOwnProperty('partitionKeysOrError')
        ? overrides.partitionKeysOrError!
        : relationshipsToOmit.has('PartitionKeys')
        ? ({} as PartitionKeys)
        : buildPartitionKeys({}, relationshipsToOmit),
  };
};

export const buildMessageEvent = (
  overrides?: Partial<MessageEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MessageEvent'} & MessageEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MessageEvent');
  return {
    __typename: 'MessageEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<MetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MetadataEntry'} & MetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MetadataEntry');
  return {
    __typename: 'MetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'laborum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'aut',
  };
};

export const buildMetadataItemDefinition = (
  overrides?: Partial<MetadataItemDefinition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MetadataItemDefinition'} & MetadataItemDefinition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MetadataItemDefinition');
  return {
    __typename: 'MetadataItemDefinition',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'ex',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'quasi',
  };
};

export const buildMissingAutoMaterializeCondition = (
  overrides?: Partial<MissingAutoMaterializeCondition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MissingAutoMaterializeCondition'} & MissingAutoMaterializeCondition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MissingAutoMaterializeCondition');
  return {
    __typename: 'MissingAutoMaterializeCondition',
    decisionType:
      overrides && overrides.hasOwnProperty('decisionType')
        ? overrides.decisionType!
        : AutoMaterializeDecisionType.DISCARD,
    partitionKeysOrError:
      overrides && overrides.hasOwnProperty('partitionKeysOrError')
        ? overrides.partitionKeysOrError!
        : relationshipsToOmit.has('PartitionKeys')
        ? ({} as PartitionKeys)
        : buildPartitionKeys({}, relationshipsToOmit),
  };
};

export const buildMissingFieldConfigError = (
  overrides?: Partial<MissingFieldConfigError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MissingFieldConfigError'} & MissingFieldConfigError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MissingFieldConfigError');
  return {
    __typename: 'MissingFieldConfigError',
    field:
      overrides && overrides.hasOwnProperty('field')
        ? overrides.field!
        : relationshipsToOmit.has('ConfigTypeField')
        ? ({} as ConfigTypeField)
        : buildConfigTypeField({}, relationshipsToOmit),
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'autem',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : [],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : EvaluationErrorReason.FIELDS_NOT_DEFINED,
    stack:
      overrides && overrides.hasOwnProperty('stack')
        ? overrides.stack!
        : relationshipsToOmit.has('EvaluationStack')
        ? ({} as EvaluationStack)
        : buildEvaluationStack({}, relationshipsToOmit),
  };
};

export const buildMissingFieldsConfigError = (
  overrides?: Partial<MissingFieldsConfigError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MissingFieldsConfigError'} & MissingFieldsConfigError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MissingFieldsConfigError');
  return {
    __typename: 'MissingFieldsConfigError',
    fields: overrides && overrides.hasOwnProperty('fields') ? overrides.fields! : [],
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'voluptatibus',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : [],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : EvaluationErrorReason.FIELDS_NOT_DEFINED,
    stack:
      overrides && overrides.hasOwnProperty('stack')
        ? overrides.stack!
        : relationshipsToOmit.has('EvaluationStack')
        ? ({} as EvaluationStack)
        : buildEvaluationStack({}, relationshipsToOmit),
  };
};

export const buildMissingRunIdErrorEvent = (
  overrides?: Partial<MissingRunIdErrorEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MissingRunIdErrorEvent'} & MissingRunIdErrorEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MissingRunIdErrorEvent');
  return {
    __typename: 'MissingRunIdErrorEvent',
    invalidRunId:
      overrides && overrides.hasOwnProperty('invalidRunId') ? overrides.invalidRunId! : 'quis',
  };
};

export const buildMode = (
  overrides?: Partial<Mode>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Mode'} & Mode => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Mode');
  return {
    __typename: 'Mode',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'dolor',
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'quia',
    loggers: overrides && overrides.hasOwnProperty('loggers') ? overrides.loggers! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'aliquam',
    resources: overrides && overrides.hasOwnProperty('resources') ? overrides.resources! : [],
  };
};

export const buildModeNotFoundError = (
  overrides?: Partial<ModeNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ModeNotFoundError'} & ModeNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ModeNotFoundError');
  return {
    __typename: 'ModeNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'eius',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'dolorem',
  };
};

export const buildMultiPartitionStatuses = (
  overrides?: Partial<MultiPartitionStatuses>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'MultiPartitionStatuses'} & MultiPartitionStatuses => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('MultiPartitionStatuses');
  return {
    __typename: 'MultiPartitionStatuses',
    primaryDimensionName:
      overrides && overrides.hasOwnProperty('primaryDimensionName')
        ? overrides.primaryDimensionName!
        : 'ea',
    ranges: overrides && overrides.hasOwnProperty('ranges') ? overrides.ranges! : [],
  };
};

export const buildNestedResourceEntry = (
  overrides?: Partial<NestedResourceEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'NestedResourceEntry'} & NestedResourceEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('NestedResourceEntry');
  return {
    __typename: 'NestedResourceEntry',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'quia',
    resource:
      overrides && overrides.hasOwnProperty('resource')
        ? overrides.resource!
        : relationshipsToOmit.has('ResourceDetails')
        ? ({} as ResourceDetails)
        : buildResourceDetails({}, relationshipsToOmit),
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : NestedResourceType.ANONYMOUS,
  };
};

export const buildNoModeProvidedError = (
  overrides?: Partial<NoModeProvidedError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'NoModeProvidedError'} & NoModeProvidedError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('NoModeProvidedError');
  return {
    __typename: 'NoModeProvidedError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'neque',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'quidem',
  };
};

export const buildNodeInvocationSite = (
  overrides?: Partial<NodeInvocationSite>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'NodeInvocationSite'} & NodeInvocationSite => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('NodeInvocationSite');
  return {
    __typename: 'NodeInvocationSite',
    pipeline:
      overrides && overrides.hasOwnProperty('pipeline')
        ? overrides.pipeline!
        : relationshipsToOmit.has('Pipeline')
        ? ({} as Pipeline)
        : buildPipeline({}, relationshipsToOmit),
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : relationshipsToOmit.has('SolidHandle')
        ? ({} as SolidHandle)
        : buildSolidHandle({}, relationshipsToOmit),
  };
};

export const buildNotebookMetadataEntry = (
  overrides?: Partial<NotebookMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'NotebookMetadataEntry'} & NotebookMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('NotebookMetadataEntry');
  return {
    __typename: 'NotebookMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quis',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'aut',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : 'reprehenderit',
  };
};

export const buildNullMetadataEntry = (
  overrides?: Partial<NullMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'NullMetadataEntry'} & NullMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('NullMetadataEntry');
  return {
    __typename: 'NullMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'molestias',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'dolorem',
  };
};

export const buildNullableConfigType = (
  overrides?: Partial<NullableConfigType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'NullableConfigType'} & NullableConfigType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('NullableConfigType');
  return {
    __typename: 'NullableConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'voluptas',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'consequuntur',
    ofType:
      overrides && overrides.hasOwnProperty('ofType')
        ? overrides.ofType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys') ? overrides.typeParamKeys! : [],
  };
};

export const buildNullableDagsterType = (
  overrides?: Partial<NullableDagsterType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'NullableDagsterType'} & NullableDagsterType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('NullableDagsterType');
  return {
    __typename: 'NullableDagsterType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'ea',
    displayName:
      overrides && overrides.hasOwnProperty('displayName')
        ? overrides.displayName!
        : 'necessitatibus',
    innerTypes: overrides && overrides.hasOwnProperty('innerTypes') ? overrides.innerTypes! : [],
    inputSchemaType:
      overrides && overrides.hasOwnProperty('inputSchemaType')
        ? overrides.inputSchemaType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    isBuiltin: overrides && overrides.hasOwnProperty('isBuiltin') ? overrides.isBuiltin! : false,
    isList: overrides && overrides.hasOwnProperty('isList') ? overrides.isList! : false,
    isNothing: overrides && overrides.hasOwnProperty('isNothing') ? overrides.isNothing! : true,
    isNullable: overrides && overrides.hasOwnProperty('isNullable') ? overrides.isNullable! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'perferendis',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'nulla',
    ofType:
      overrides && overrides.hasOwnProperty('ofType')
        ? overrides.ofType!
        : relationshipsToOmit.has('DagsterType')
        ? ({} as DagsterType)
        : buildDagsterType({}, relationshipsToOmit),
    outputSchemaType:
      overrides && overrides.hasOwnProperty('outputSchemaType')
        ? overrides.outputSchemaType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
  };
};

export const buildObjectStoreOperationEvent = (
  overrides?: Partial<ObjectStoreOperationEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ObjectStoreOperationEvent'} & ObjectStoreOperationEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ObjectStoreOperationEvent');
  return {
    __typename: 'ObjectStoreOperationEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
    operationResult:
      overrides && overrides.hasOwnProperty('operationResult')
        ? overrides.operationResult!
        : relationshipsToOmit.has('ObjectStoreOperationResult')
        ? ({} as ObjectStoreOperationResult)
        : buildObjectStoreOperationResult({}, relationshipsToOmit),
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
  overrides?: Partial<ObjectStoreOperationResult>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ObjectStoreOperationResult'} & ObjectStoreOperationResult => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ObjectStoreOperationResult');
  return {
    __typename: 'ObjectStoreOperationResult',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'porro',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'nobis',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    op:
      overrides && overrides.hasOwnProperty('op')
        ? overrides.op!
        : ObjectStoreOperationType.CP_OBJECT,
  };
};

export const buildObservationEvent = (
  overrides?: Partial<ObservationEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ObservationEvent'} & ObservationEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ObservationEvent');
  return {
    __typename: 'ObservationEvent',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'dolorum',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'non',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ratione',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    partition: overrides && overrides.hasOwnProperty('partition') ? overrides.partition! : 'esse',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'aliquid',
    runOrError:
      overrides && overrides.hasOwnProperty('runOrError')
        ? overrides.runOrError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID')
        ? overrides.solidHandleID!
        : 'possimus',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'magnam',
    stepStats:
      overrides && overrides.hasOwnProperty('stepStats')
        ? overrides.stepStats!
        : relationshipsToOmit.has('RunStepStats')
        ? ({} as RunStepStats)
        : buildRunStepStats({}, relationshipsToOmit),
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'ut',
  };
};

export const buildOutput = (
  overrides?: Partial<Output>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Output'} & Output => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Output');
  return {
    __typename: 'Output',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : relationshipsToOmit.has('OutputDefinition')
        ? ({} as OutputDefinition)
        : buildOutputDefinition({}, relationshipsToOmit),
    dependedBy: overrides && overrides.hasOwnProperty('dependedBy') ? overrides.dependedBy! : [],
    solid:
      overrides && overrides.hasOwnProperty('solid')
        ? overrides.solid!
        : relationshipsToOmit.has('Solid')
        ? ({} as Solid)
        : buildSolid({}, relationshipsToOmit),
  };
};

export const buildOutputDefinition = (
  overrides?: Partial<OutputDefinition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'OutputDefinition'} & OutputDefinition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('OutputDefinition');
  return {
    __typename: 'OutputDefinition',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quis',
    isDynamic: overrides && overrides.hasOwnProperty('isDynamic') ? overrides.isDynamic! : false,
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'repellendus',
    solidDefinition:
      overrides && overrides.hasOwnProperty('solidDefinition')
        ? overrides.solidDefinition!
        : relationshipsToOmit.has('SolidDefinition')
        ? ({} as SolidDefinition)
        : buildSolidDefinition({}, relationshipsToOmit),
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : relationshipsToOmit.has('DagsterType')
        ? ({} as DagsterType)
        : buildDagsterType({}, relationshipsToOmit),
  };
};

export const buildOutputMapping = (
  overrides?: Partial<OutputMapping>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'OutputMapping'} & OutputMapping => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('OutputMapping');
  return {
    __typename: 'OutputMapping',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : relationshipsToOmit.has('OutputDefinition')
        ? ({} as OutputDefinition)
        : buildOutputDefinition({}, relationshipsToOmit),
    mappedOutput:
      overrides && overrides.hasOwnProperty('mappedOutput')
        ? overrides.mappedOutput!
        : relationshipsToOmit.has('Output')
        ? ({} as Output)
        : buildOutput({}, relationshipsToOmit),
  };
};

export const buildParentMaterializedAutoMaterializeCondition = (
  overrides?: Partial<ParentMaterializedAutoMaterializeCondition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {
  __typename: 'ParentMaterializedAutoMaterializeCondition';
} & ParentMaterializedAutoMaterializeCondition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ParentMaterializedAutoMaterializeCondition');
  return {
    __typename: 'ParentMaterializedAutoMaterializeCondition',
    decisionType:
      overrides && overrides.hasOwnProperty('decisionType')
        ? overrides.decisionType!
        : AutoMaterializeDecisionType.DISCARD,
    partitionKeysOrError:
      overrides && overrides.hasOwnProperty('partitionKeysOrError')
        ? overrides.partitionKeysOrError!
        : relationshipsToOmit.has('PartitionKeys')
        ? ({} as PartitionKeys)
        : buildPartitionKeys({}, relationshipsToOmit),
  };
};

export const buildParentOutdatedAutoMaterializeCondition = (
  overrides?: Partial<ParentOutdatedAutoMaterializeCondition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {
  __typename: 'ParentOutdatedAutoMaterializeCondition';
} & ParentOutdatedAutoMaterializeCondition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ParentOutdatedAutoMaterializeCondition');
  return {
    __typename: 'ParentOutdatedAutoMaterializeCondition',
    decisionType:
      overrides && overrides.hasOwnProperty('decisionType')
        ? overrides.decisionType!
        : AutoMaterializeDecisionType.DISCARD,
    partitionKeysOrError:
      overrides && overrides.hasOwnProperty('partitionKeysOrError')
        ? overrides.partitionKeysOrError!
        : relationshipsToOmit.has('PartitionKeys')
        ? ({} as PartitionKeys)
        : buildPartitionKeys({}, relationshipsToOmit),
    waitingOnAssetKeys:
      overrides && overrides.hasOwnProperty('waitingOnAssetKeys')
        ? overrides.waitingOnAssetKeys!
        : [],
  };
};

export const buildPartition = (
  overrides?: Partial<Partition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Partition'} & Partition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Partition');
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
        : relationshipsToOmit.has('PartitionRunConfig')
        ? ({} as PartitionRunConfig)
        : buildPartitionRunConfig({}, relationshipsToOmit),
    runs: overrides && overrides.hasOwnProperty('runs') ? overrides.runs! : [],
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
    status:
      overrides && overrides.hasOwnProperty('status') ? overrides.status! : RunStatus.CANCELED,
    tagsOrError:
      overrides && overrides.hasOwnProperty('tagsOrError')
        ? overrides.tagsOrError!
        : relationshipsToOmit.has('PartitionTags')
        ? ({} as PartitionTags)
        : buildPartitionTags({}, relationshipsToOmit),
  };
};

export const buildPartitionBackfill = (
  overrides?: Partial<PartitionBackfill>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionBackfill'} & PartitionBackfill => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionBackfill');
  return {
    __typename: 'PartitionBackfill',
    assetBackfillData:
      overrides && overrides.hasOwnProperty('assetBackfillData')
        ? overrides.assetBackfillData!
        : relationshipsToOmit.has('AssetBackfillData')
        ? ({} as AssetBackfillData)
        : buildAssetBackfillData({}, relationshipsToOmit),
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection') ? overrides.assetSelection! : [],
    endTimestamp:
      overrides && overrides.hasOwnProperty('endTimestamp') ? overrides.endTimestamp! : 0.33,
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
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
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'recusandae',
    isAssetBackfill:
      overrides && overrides.hasOwnProperty('isAssetBackfill') ? overrides.isAssetBackfill! : false,
    isValidSerialization:
      overrides && overrides.hasOwnProperty('isValidSerialization')
        ? overrides.isValidSerialization!
        : false,
    numCancelable:
      overrides && overrides.hasOwnProperty('numCancelable') ? overrides.numCancelable! : 53,
    numPartitions:
      overrides && overrides.hasOwnProperty('numPartitions') ? overrides.numPartitions! : 4165,
    partitionNames:
      overrides && overrides.hasOwnProperty('partitionNames') ? overrides.partitionNames! : [],
    partitionSet:
      overrides && overrides.hasOwnProperty('partitionSet')
        ? overrides.partitionSet!
        : relationshipsToOmit.has('PartitionSet')
        ? ({} as PartitionSet)
        : buildPartitionSet({}, relationshipsToOmit),
    partitionSetName:
      overrides && overrides.hasOwnProperty('partitionSetName')
        ? overrides.partitionSetName!
        : 'quis',
    partitionStatusCounts:
      overrides && overrides.hasOwnProperty('partitionStatusCounts')
        ? overrides.partitionStatusCounts!
        : [],
    partitionStatuses:
      overrides && overrides.hasOwnProperty('partitionStatuses')
        ? overrides.partitionStatuses!
        : relationshipsToOmit.has('PartitionStatuses')
        ? ({} as PartitionStatuses)
        : buildPartitionStatuses({}, relationshipsToOmit),
    reexecutionSteps:
      overrides && overrides.hasOwnProperty('reexecutionSteps') ? overrides.reexecutionSteps! : [],
    runs: overrides && overrides.hasOwnProperty('runs') ? overrides.runs! : [],
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : BulkActionStatus.CANCELED,
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 8.28,
    unfinishedRuns:
      overrides && overrides.hasOwnProperty('unfinishedRuns') ? overrides.unfinishedRuns! : [],
    user: overrides && overrides.hasOwnProperty('user') ? overrides.user! : 'eius',
  };
};

export const buildPartitionBackfills = (
  overrides?: Partial<PartitionBackfills>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionBackfills'} & PartitionBackfills => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionBackfills');
  return {
    __typename: 'PartitionBackfills',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildPartitionDefinition = (
  overrides?: Partial<PartitionDefinition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionDefinition'} & PartitionDefinition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionDefinition');
  return {
    __typename: 'PartitionDefinition',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'ab',
    dimensionTypes:
      overrides && overrides.hasOwnProperty('dimensionTypes') ? overrides.dimensionTypes! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'facilis',
    type:
      overrides && overrides.hasOwnProperty('type')
        ? overrides.type!
        : PartitionDefinitionType.DYNAMIC,
  };
};

export const buildPartitionKeyRange = (
  overrides?: Partial<PartitionKeyRange>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionKeyRange'} & PartitionKeyRange => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionKeyRange');
  return {
    __typename: 'PartitionKeyRange',
    end: overrides && overrides.hasOwnProperty('end') ? overrides.end! : 'repudiandae',
    start: overrides && overrides.hasOwnProperty('start') ? overrides.start! : 'qui',
  };
};

export const buildPartitionKeys = (
  overrides?: Partial<PartitionKeys>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionKeys'} & PartitionKeys => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionKeys');
  return {
    __typename: 'PartitionKeys',
    partitionKeys:
      overrides && overrides.hasOwnProperty('partitionKeys') ? overrides.partitionKeys! : [],
  };
};

export const buildPartitionRun = (
  overrides?: Partial<PartitionRun>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionRun'} & PartitionRun => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionRun');
  return {
    __typename: 'PartitionRun',
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'ut',
    partitionName:
      overrides && overrides.hasOwnProperty('partitionName') ? overrides.partitionName! : 'enim',
    run:
      overrides && overrides.hasOwnProperty('run')
        ? overrides.run!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
  };
};

export const buildPartitionRunConfig = (
  overrides?: Partial<PartitionRunConfig>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionRunConfig'} & PartitionRunConfig => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionRunConfig');
  return {
    __typename: 'PartitionRunConfig',
    yaml: overrides && overrides.hasOwnProperty('yaml') ? overrides.yaml! : 'ab',
  };
};

export const buildPartitionSet = (
  overrides?: Partial<PartitionSet>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionSet'} & PartitionSet => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionSet');
  return {
    __typename: 'PartitionSet',
    backfills: overrides && overrides.hasOwnProperty('backfills') ? overrides.backfills! : [],
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'e0ac1103-209e-4984-89c5-ba61a9d9b9f1',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'cupiditate',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'placeat',
    partition:
      overrides && overrides.hasOwnProperty('partition')
        ? overrides.partition!
        : relationshipsToOmit.has('Partition')
        ? ({} as Partition)
        : buildPartition({}, relationshipsToOmit),
    partitionRuns:
      overrides && overrides.hasOwnProperty('partitionRuns') ? overrides.partitionRuns! : [],
    partitionStatusesOrError:
      overrides && overrides.hasOwnProperty('partitionStatusesOrError')
        ? overrides.partitionStatusesOrError!
        : relationshipsToOmit.has('PartitionStatuses')
        ? ({} as PartitionStatuses)
        : buildPartitionStatuses({}, relationshipsToOmit),
    partitionsOrError:
      overrides && overrides.hasOwnProperty('partitionsOrError')
        ? overrides.partitionsOrError!
        : relationshipsToOmit.has('Partitions')
        ? ({} as Partitions)
        : buildPartitions({}, relationshipsToOmit),
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'nihil',
    repositoryOrigin:
      overrides && overrides.hasOwnProperty('repositoryOrigin')
        ? overrides.repositoryOrigin!
        : relationshipsToOmit.has('RepositoryOrigin')
        ? ({} as RepositoryOrigin)
        : buildRepositoryOrigin({}, relationshipsToOmit),
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
  };
};

export const buildPartitionSetNotFoundError = (
  overrides?: Partial<PartitionSetNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionSetNotFoundError'} & PartitionSetNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionSetNotFoundError');
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
  overrides?: Partial<PartitionSetSelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): PartitionSetSelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionSetSelector');
  return {
    partitionSetName:
      overrides && overrides.hasOwnProperty('partitionSetName')
        ? overrides.partitionSetName!
        : 'soluta',
    repositorySelector:
      overrides && overrides.hasOwnProperty('repositorySelector')
        ? overrides.repositorySelector!
        : relationshipsToOmit.has('RepositorySelector')
        ? ({} as RepositorySelector)
        : buildRepositorySelector({}, relationshipsToOmit),
  };
};

export const buildPartitionSets = (
  overrides?: Partial<PartitionSets>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionSets'} & PartitionSets => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionSets');
  return {
    __typename: 'PartitionSets',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildPartitionStats = (
  overrides?: Partial<PartitionStats>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionStats'} & PartitionStats => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionStats');
  return {
    __typename: 'PartitionStats',
    numFailed: overrides && overrides.hasOwnProperty('numFailed') ? overrides.numFailed! : 4790,
    numMaterialized:
      overrides && overrides.hasOwnProperty('numMaterialized') ? overrides.numMaterialized! : 9478,
    numMaterializing:
      overrides && overrides.hasOwnProperty('numMaterializing')
        ? overrides.numMaterializing!
        : 4213,
    numPartitions:
      overrides && overrides.hasOwnProperty('numPartitions') ? overrides.numPartitions! : 4096,
  };
};

export const buildPartitionStatus = (
  overrides?: Partial<PartitionStatus>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionStatus'} & PartitionStatus => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionStatus');
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
        : RunStatus.CANCELED,
  };
};

export const buildPartitionStatusCounts = (
  overrides?: Partial<PartitionStatusCounts>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionStatusCounts'} & PartitionStatusCounts => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionStatusCounts');
  return {
    __typename: 'PartitionStatusCounts',
    count: overrides && overrides.hasOwnProperty('count') ? overrides.count! : 5809,
    runStatus:
      overrides && overrides.hasOwnProperty('runStatus')
        ? overrides.runStatus!
        : RunStatus.CANCELED,
  };
};

export const buildPartitionStatuses = (
  overrides?: Partial<PartitionStatuses>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionStatuses'} & PartitionStatuses => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionStatuses');
  return {
    __typename: 'PartitionStatuses',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildPartitionSubsetDeserializationError = (
  overrides?: Partial<PartitionSubsetDeserializationError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionSubsetDeserializationError'} & PartitionSubsetDeserializationError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionSubsetDeserializationError');
  return {
    __typename: 'PartitionSubsetDeserializationError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'beatae',
  };
};

export const buildPartitionTags = (
  overrides?: Partial<PartitionTags>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PartitionTags'} & PartitionTags => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PartitionTags');
  return {
    __typename: 'PartitionTags',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildPartitions = (
  overrides?: Partial<Partitions>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Partitions'} & Partitions => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Partitions');
  return {
    __typename: 'Partitions',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildPathMetadataEntry = (
  overrides?: Partial<PathMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PathMetadataEntry'} & PathMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PathMetadataEntry');
  return {
    __typename: 'PathMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'et',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'rerum',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : 'soluta',
  };
};

export const buildPermission = (
  overrides?: Partial<Permission>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Permission'} & Permission => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Permission');
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
  overrides?: Partial<Pipeline>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Pipeline'} & Pipeline => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Pipeline');
  return {
    __typename: 'Pipeline',
    dagsterTypeOrError:
      overrides && overrides.hasOwnProperty('dagsterTypeOrError')
        ? overrides.dagsterTypeOrError!
        : relationshipsToOmit.has('DagsterTypeNotFoundError')
        ? ({} as DagsterTypeNotFoundError)
        : buildDagsterTypeNotFoundError({}, relationshipsToOmit),
    dagsterTypes:
      overrides && overrides.hasOwnProperty('dagsterTypes') ? overrides.dagsterTypes! : [],
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
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    modes: overrides && overrides.hasOwnProperty('modes') ? overrides.modes! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'veritatis',
    parentSnapshotId:
      overrides && overrides.hasOwnProperty('parentSnapshotId')
        ? overrides.parentSnapshotId!
        : 'et',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'aperiam',
    presets: overrides && overrides.hasOwnProperty('presets') ? overrides.presets! : [],
    repository:
      overrides && overrides.hasOwnProperty('repository')
        ? overrides.repository!
        : relationshipsToOmit.has('Repository')
        ? ({} as Repository)
        : buildRepository({}, relationshipsToOmit),
    runs: overrides && overrides.hasOwnProperty('runs') ? overrides.runs! : [],
    schedules: overrides && overrides.hasOwnProperty('schedules') ? overrides.schedules! : [],
    sensors: overrides && overrides.hasOwnProperty('sensors') ? overrides.sensors! : [],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : relationshipsToOmit.has('SolidHandle')
        ? ({} as SolidHandle)
        : buildSolidHandle({}, relationshipsToOmit),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles') ? overrides.solidHandles! : [],
    solids: overrides && overrides.hasOwnProperty('solids') ? overrides.solids! : [],
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildPipelineConfigValidationError = (
  overrides?: Partial<PipelineConfigValidationError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineConfigValidationError'} & PipelineConfigValidationError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineConfigValidationError');
  return {
    __typename: 'PipelineConfigValidationError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'consequatur',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : [],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : EvaluationErrorReason.FIELDS_NOT_DEFINED,
    stack:
      overrides && overrides.hasOwnProperty('stack')
        ? overrides.stack!
        : relationshipsToOmit.has('EvaluationStack')
        ? ({} as EvaluationStack)
        : buildEvaluationStack({}, relationshipsToOmit),
  };
};

export const buildPipelineConfigValidationInvalid = (
  overrides?: Partial<PipelineConfigValidationInvalid>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineConfigValidationInvalid'} & PipelineConfigValidationInvalid => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineConfigValidationInvalid');
  return {
    __typename: 'PipelineConfigValidationInvalid',
    errors: overrides && overrides.hasOwnProperty('errors') ? overrides.errors! : [],
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'totam',
  };
};

export const buildPipelineConfigValidationValid = (
  overrides?: Partial<PipelineConfigValidationValid>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineConfigValidationValid'} & PipelineConfigValidationValid => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineConfigValidationValid');
  return {
    __typename: 'PipelineConfigValidationValid',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'veniam',
  };
};

export const buildPipelineNotFoundError = (
  overrides?: Partial<PipelineNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineNotFoundError'} & PipelineNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineNotFoundError');
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
  overrides?: Partial<PipelinePreset>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelinePreset'} & PipelinePreset => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelinePreset');
  return {
    __typename: 'PipelinePreset',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'aperiam',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'saepe',
    runConfigYaml:
      overrides && overrides.hasOwnProperty('runConfigYaml') ? overrides.runConfigYaml! : 'et',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildPipelineReference = (
  overrides?: Partial<PipelineReference>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineReference'} & PipelineReference => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineReference');
  return {
    __typename: 'PipelineReference',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'iure',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
  };
};

export const buildPipelineRun = (
  overrides?: Partial<PipelineRun>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineRun'} & PipelineRun => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineRun');
  return {
    __typename: 'PipelineRun',
    assets: overrides && overrides.hasOwnProperty('assets') ? overrides.assets! : [],
    canTerminate:
      overrides && overrides.hasOwnProperty('canTerminate') ? overrides.canTerminate! : false,
    capturedLogs:
      overrides && overrides.hasOwnProperty('capturedLogs')
        ? overrides.capturedLogs!
        : relationshipsToOmit.has('CapturedLogs')
        ? ({} as CapturedLogs)
        : buildCapturedLogs({}, relationshipsToOmit),
    computeLogs:
      overrides && overrides.hasOwnProperty('computeLogs')
        ? overrides.computeLogs!
        : relationshipsToOmit.has('ComputeLogs')
        ? ({} as ComputeLogs)
        : buildComputeLogs({}, relationshipsToOmit),
    eventConnection:
      overrides && overrides.hasOwnProperty('eventConnection')
        ? overrides.eventConnection!
        : relationshipsToOmit.has('EventConnection')
        ? ({} as EventConnection)
        : buildEventConnection({}, relationshipsToOmit),
    executionPlan:
      overrides && overrides.hasOwnProperty('executionPlan')
        ? overrides.executionPlan!
        : relationshipsToOmit.has('ExecutionPlan')
        ? ({} as ExecutionPlan)
        : buildExecutionPlan({}, relationshipsToOmit),
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
        : relationshipsToOmit.has('PipelineReference')
        ? ({} as PipelineReference)
        : buildPipelineReference({}, relationshipsToOmit),
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'animi',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'fugiat',
    repositoryOrigin:
      overrides && overrides.hasOwnProperty('repositoryOrigin')
        ? overrides.repositoryOrigin!
        : relationshipsToOmit.has('RepositoryOrigin')
        ? ({} as RepositoryOrigin)
        : buildRepositoryOrigin({}, relationshipsToOmit),
    rootRunId: overrides && overrides.hasOwnProperty('rootRunId') ? overrides.rootRunId! : 'quia',
    runConfig:
      overrides && overrides.hasOwnProperty('runConfig') ? overrides.runConfig! : 'aspernatur',
    runConfigYaml:
      overrides && overrides.hasOwnProperty('runConfigYaml') ? overrides.runConfigYaml! : 'facere',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'tenetur',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
    stats:
      overrides && overrides.hasOwnProperty('stats')
        ? overrides.stats!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    status:
      overrides && overrides.hasOwnProperty('status') ? overrides.status! : RunStatus.CANCELED,
    stepKeysToExecute:
      overrides && overrides.hasOwnProperty('stepKeysToExecute')
        ? overrides.stepKeysToExecute!
        : [],
    stepStats: overrides && overrides.hasOwnProperty('stepStats') ? overrides.stepStats! : [],
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildPipelineRunConflict = (
  overrides?: Partial<PipelineRunConflict>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineRunConflict'} & PipelineRunConflict => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineRunConflict');
  return {
    __typename: 'PipelineRunConflict',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'in',
  };
};

export const buildPipelineRunLogsSubscriptionFailure = (
  overrides?: Partial<PipelineRunLogsSubscriptionFailure>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineRunLogsSubscriptionFailure'} & PipelineRunLogsSubscriptionFailure => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineRunLogsSubscriptionFailure');
  return {
    __typename: 'PipelineRunLogsSubscriptionFailure',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'vitae',
    missingRunId:
      overrides && overrides.hasOwnProperty('missingRunId') ? overrides.missingRunId! : 'cumque',
  };
};

export const buildPipelineRunLogsSubscriptionSuccess = (
  overrides?: Partial<PipelineRunLogsSubscriptionSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineRunLogsSubscriptionSuccess'} & PipelineRunLogsSubscriptionSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineRunLogsSubscriptionSuccess');
  return {
    __typename: 'PipelineRunLogsSubscriptionSuccess',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'id',
    hasMorePastEvents:
      overrides && overrides.hasOwnProperty('hasMorePastEvents')
        ? overrides.hasMorePastEvents!
        : true,
    messages: overrides && overrides.hasOwnProperty('messages') ? overrides.messages! : [],
    run:
      overrides && overrides.hasOwnProperty('run')
        ? overrides.run!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
  };
};

export const buildPipelineRunMetadataEntry = (
  overrides?: Partial<PipelineRunMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineRunMetadataEntry'} & PipelineRunMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineRunMetadataEntry');
  return {
    __typename: 'PipelineRunMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'adipisci',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'soluta',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'dolorem',
  };
};

export const buildPipelineRunNotFoundError = (
  overrides?: Partial<PipelineRunNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineRunNotFoundError'} & PipelineRunNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineRunNotFoundError');
  return {
    __typename: 'PipelineRunNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'minus',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'rerum',
  };
};

export const buildPipelineRunStatsSnapshot = (
  overrides?: Partial<PipelineRunStatsSnapshot>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineRunStatsSnapshot'} & PipelineRunStatsSnapshot => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineRunStatsSnapshot');
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
  overrides?: Partial<PipelineRunStepStats>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineRunStepStats'} & PipelineRunStepStats => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineRunStepStats');
  return {
    __typename: 'PipelineRunStepStats',
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 3.31,
    expectationResults:
      overrides && overrides.hasOwnProperty('expectationResults')
        ? overrides.expectationResults!
        : [],
    materializations:
      overrides && overrides.hasOwnProperty('materializations') ? overrides.materializations! : [],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'et',
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 8.43,
    status:
      overrides && overrides.hasOwnProperty('status') ? overrides.status! : StepEventStatus.FAILURE,
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'reiciendis',
  };
};

export const buildPipelineRuns = (
  overrides?: Partial<PipelineRuns>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineRuns'} & PipelineRuns => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineRuns');
  return {
    __typename: 'PipelineRuns',
    count: overrides && overrides.hasOwnProperty('count') ? overrides.count! : 1847,
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildPipelineSelector = (
  overrides?: Partial<PipelineSelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): PipelineSelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineSelector');
  return {
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection') ? overrides.assetSelection! : [],
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
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
  };
};

export const buildPipelineSnapshot = (
  overrides?: Partial<PipelineSnapshot>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineSnapshot'} & PipelineSnapshot => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineSnapshot');
  return {
    __typename: 'PipelineSnapshot',
    dagsterTypeOrError:
      overrides && overrides.hasOwnProperty('dagsterTypeOrError')
        ? overrides.dagsterTypeOrError!
        : relationshipsToOmit.has('DagsterTypeNotFoundError')
        ? ({} as DagsterTypeNotFoundError)
        : buildDagsterTypeNotFoundError({}, relationshipsToOmit),
    dagsterTypes:
      overrides && overrides.hasOwnProperty('dagsterTypes') ? overrides.dagsterTypes! : [],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'corporis',
    graphName:
      overrides && overrides.hasOwnProperty('graphName') ? overrides.graphName! : 'dolorum',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'a052bf7d-6918-434c-b95b-82d9dc5b3fb1',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    modes: overrides && overrides.hasOwnProperty('modes') ? overrides.modes! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'beatae',
    parentSnapshotId:
      overrides && overrides.hasOwnProperty('parentSnapshotId')
        ? overrides.parentSnapshotId!
        : 'ut',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'labore',
    runs: overrides && overrides.hasOwnProperty('runs') ? overrides.runs! : [],
    schedules: overrides && overrides.hasOwnProperty('schedules') ? overrides.schedules! : [],
    sensors: overrides && overrides.hasOwnProperty('sensors') ? overrides.sensors! : [],
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : relationshipsToOmit.has('SolidHandle')
        ? ({} as SolidHandle)
        : buildSolidHandle({}, relationshipsToOmit),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles') ? overrides.solidHandles! : [],
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
    solids: overrides && overrides.hasOwnProperty('solids') ? overrides.solids! : [],
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildPipelineSnapshotNotFoundError = (
  overrides?: Partial<PipelineSnapshotNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineSnapshotNotFoundError'} & PipelineSnapshotNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineSnapshotNotFoundError');
  return {
    __typename: 'PipelineSnapshotNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'sit',
    snapshotId:
      overrides && overrides.hasOwnProperty('snapshotId') ? overrides.snapshotId! : 'quibusdam',
  };
};

export const buildPipelineTag = (
  overrides?: Partial<PipelineTag>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineTag'} & PipelineTag => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineTag');
  return {
    __typename: 'PipelineTag',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'qui',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'et',
  };
};

export const buildPipelineTagAndValues = (
  overrides?: Partial<PipelineTagAndValues>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PipelineTagAndValues'} & PipelineTagAndValues => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PipelineTagAndValues');
  return {
    __typename: 'PipelineTagAndValues',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'repudiandae',
    values: overrides && overrides.hasOwnProperty('values') ? overrides.values! : [],
  };
};

export const buildPresetNotFoundError = (
  overrides?: Partial<PresetNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PresetNotFoundError'} & PresetNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PresetNotFoundError');
  return {
    __typename: 'PresetNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'provident',
    preset: overrides && overrides.hasOwnProperty('preset') ? overrides.preset! : 'necessitatibus',
  };
};

export const buildPythonArtifactMetadataEntry = (
  overrides?: Partial<PythonArtifactMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PythonArtifactMetadataEntry'} & PythonArtifactMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PythonArtifactMetadataEntry');
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
  overrides?: Partial<PythonError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'PythonError'} & PythonError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('PythonError');
  return {
    __typename: 'PythonError',
    cause:
      overrides && overrides.hasOwnProperty('cause')
        ? overrides.cause!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    causes: overrides && overrides.hasOwnProperty('causes') ? overrides.causes! : [],
    className: overrides && overrides.hasOwnProperty('className') ? overrides.className! : 'magni',
    errorChain: overrides && overrides.hasOwnProperty('errorChain') ? overrides.errorChain! : [],
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'veritatis',
    stack: overrides && overrides.hasOwnProperty('stack') ? overrides.stack! : [],
  };
};

export const buildReexecutionParams = (
  overrides?: Partial<ReexecutionParams>,
  _relationshipsToOmit: Set<string> = new Set(),
): ReexecutionParams => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ReexecutionParams');
  return {
    parentRunId:
      overrides && overrides.hasOwnProperty('parentRunId') ? overrides.parentRunId! : 'sunt',
    strategy:
      overrides && overrides.hasOwnProperty('strategy')
        ? overrides.strategy!
        : ReexecutionStrategy.ALL_STEPS,
  };
};

export const buildRegularConfigType = (
  overrides?: Partial<RegularConfigType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RegularConfigType'} & RegularConfigType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RegularConfigType');
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
        : [],
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys') ? overrides.typeParamKeys! : [],
  };
};

export const buildRegularDagsterType = (
  overrides?: Partial<RegularDagsterType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RegularDagsterType'} & RegularDagsterType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RegularDagsterType');
  return {
    __typename: 'RegularDagsterType',
    description:
      overrides && overrides.hasOwnProperty('description')
        ? overrides.description!
        : 'necessitatibus',
    displayName:
      overrides && overrides.hasOwnProperty('displayName') ? overrides.displayName! : 'expedita',
    innerTypes: overrides && overrides.hasOwnProperty('innerTypes') ? overrides.innerTypes! : [],
    inputSchemaType:
      overrides && overrides.hasOwnProperty('inputSchemaType')
        ? overrides.inputSchemaType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    isBuiltin: overrides && overrides.hasOwnProperty('isBuiltin') ? overrides.isBuiltin! : true,
    isList: overrides && overrides.hasOwnProperty('isList') ? overrides.isList! : false,
    isNothing: overrides && overrides.hasOwnProperty('isNothing') ? overrides.isNothing! : false,
    isNullable: overrides && overrides.hasOwnProperty('isNullable') ? overrides.isNullable! : true,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'maiores',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'velit',
    outputSchemaType:
      overrides && overrides.hasOwnProperty('outputSchemaType')
        ? overrides.outputSchemaType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
  };
};

export const buildReloadNotSupported = (
  overrides?: Partial<ReloadNotSupported>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ReloadNotSupported'} & ReloadNotSupported => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ReloadNotSupported');
  return {
    __typename: 'ReloadNotSupported',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'neque',
  };
};

export const buildReloadRepositoryLocationMutation = (
  overrides?: Partial<ReloadRepositoryLocationMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ReloadRepositoryLocationMutation'} & ReloadRepositoryLocationMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ReloadRepositoryLocationMutation');
  return {
    __typename: 'ReloadRepositoryLocationMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildReloadWorkspaceMutation = (
  overrides?: Partial<ReloadWorkspaceMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ReloadWorkspaceMutation'} & ReloadWorkspaceMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ReloadWorkspaceMutation');
  return {
    __typename: 'ReloadWorkspaceMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildRepository = (
  overrides?: Partial<Repository>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Repository'} & Repository => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Repository');
  return {
    __typename: 'Repository',
    allTopLevelResourceDetails:
      overrides && overrides.hasOwnProperty('allTopLevelResourceDetails')
        ? overrides.allTopLevelResourceDetails!
        : [],
    assetGroups: overrides && overrides.hasOwnProperty('assetGroups') ? overrides.assetGroups! : [],
    assetNodes: overrides && overrides.hasOwnProperty('assetNodes') ? overrides.assetNodes! : [],
    displayMetadata:
      overrides && overrides.hasOwnProperty('displayMetadata') ? overrides.displayMetadata! : [],
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'e97f8841-e61d-451b-93f6-99aacfac2fad',
    jobs: overrides && overrides.hasOwnProperty('jobs') ? overrides.jobs! : [],
    location:
      overrides && overrides.hasOwnProperty('location')
        ? overrides.location!
        : relationshipsToOmit.has('RepositoryLocation')
        ? ({} as RepositoryLocation)
        : buildRepositoryLocation({}, relationshipsToOmit),
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'dolor',
    origin:
      overrides && overrides.hasOwnProperty('origin')
        ? overrides.origin!
        : relationshipsToOmit.has('RepositoryOrigin')
        ? ({} as RepositoryOrigin)
        : buildRepositoryOrigin({}, relationshipsToOmit),
    partitionSets:
      overrides && overrides.hasOwnProperty('partitionSets') ? overrides.partitionSets! : [],
    pipelines: overrides && overrides.hasOwnProperty('pipelines') ? overrides.pipelines! : [],
    schedules: overrides && overrides.hasOwnProperty('schedules') ? overrides.schedules! : [],
    sensors: overrides && overrides.hasOwnProperty('sensors') ? overrides.sensors! : [],
    usedSolid:
      overrides && overrides.hasOwnProperty('usedSolid')
        ? overrides.usedSolid!
        : relationshipsToOmit.has('UsedSolid')
        ? ({} as UsedSolid)
        : buildUsedSolid({}, relationshipsToOmit),
    usedSolids: overrides && overrides.hasOwnProperty('usedSolids') ? overrides.usedSolids! : [],
  };
};

export const buildRepositoryConnection = (
  overrides?: Partial<RepositoryConnection>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RepositoryConnection'} & RepositoryConnection => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RepositoryConnection');
  return {
    __typename: 'RepositoryConnection',
    nodes: overrides && overrides.hasOwnProperty('nodes') ? overrides.nodes! : [],
  };
};

export const buildRepositoryLocation = (
  overrides?: Partial<RepositoryLocation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RepositoryLocation'} & RepositoryLocation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RepositoryLocation');
  return {
    __typename: 'RepositoryLocation',
    dagsterLibraryVersions:
      overrides && overrides.hasOwnProperty('dagsterLibraryVersions')
        ? overrides.dagsterLibraryVersions!
        : [],
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
      overrides && overrides.hasOwnProperty('repositories') ? overrides.repositories! : [],
    serverId: overrides && overrides.hasOwnProperty('serverId') ? overrides.serverId! : 'eum',
  };
};

export const buildRepositoryLocationNotFound = (
  overrides?: Partial<RepositoryLocationNotFound>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RepositoryLocationNotFound'} & RepositoryLocationNotFound => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RepositoryLocationNotFound');
  return {
    __typename: 'RepositoryLocationNotFound',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'sed',
  };
};

export const buildRepositoryMetadata = (
  overrides?: Partial<RepositoryMetadata>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RepositoryMetadata'} & RepositoryMetadata => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RepositoryMetadata');
  return {
    __typename: 'RepositoryMetadata',
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'reiciendis',
    value: overrides && overrides.hasOwnProperty('value') ? overrides.value! : 'deserunt',
  };
};

export const buildRepositoryNotFoundError = (
  overrides?: Partial<RepositoryNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RepositoryNotFoundError'} & RepositoryNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RepositoryNotFoundError');
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
  overrides?: Partial<RepositoryOrigin>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RepositoryOrigin'} & RepositoryOrigin => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RepositoryOrigin');
  return {
    __typename: 'RepositoryOrigin',
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'magni',
    repositoryLocationMetadata:
      overrides && overrides.hasOwnProperty('repositoryLocationMetadata')
        ? overrides.repositoryLocationMetadata!
        : [],
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'dolores',
    repositoryName:
      overrides && overrides.hasOwnProperty('repositoryName') ? overrides.repositoryName! : 'magni',
  };
};

export const buildRepositorySelector = (
  overrides?: Partial<RepositorySelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): RepositorySelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RepositorySelector');
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
  overrides?: Partial<Resource>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Resource'} & Resource => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Resource');
  return {
    __typename: 'Resource',
    configField:
      overrides && overrides.hasOwnProperty('configField')
        ? overrides.configField!
        : relationshipsToOmit.has('ConfigTypeField')
        ? ({} as ConfigTypeField)
        : buildConfigTypeField({}, relationshipsToOmit),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'perferendis',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'fuga',
  };
};

export const buildResourceDetails = (
  overrides?: Partial<ResourceDetails>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ResourceDetails'} & ResourceDetails => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ResourceDetails');
  return {
    __typename: 'ResourceDetails',
    assetKeysUsing:
      overrides && overrides.hasOwnProperty('assetKeysUsing') ? overrides.assetKeysUsing! : [],
    configFields:
      overrides && overrides.hasOwnProperty('configFields') ? overrides.configFields! : [],
    configuredValues:
      overrides && overrides.hasOwnProperty('configuredValues') ? overrides.configuredValues! : [],
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'laudantium',
    isTopLevel: overrides && overrides.hasOwnProperty('isTopLevel') ? overrides.isTopLevel! : false,
    jobsOpsUsing:
      overrides && overrides.hasOwnProperty('jobsOpsUsing') ? overrides.jobsOpsUsing! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'praesentium',
    nestedResources:
      overrides && overrides.hasOwnProperty('nestedResources') ? overrides.nestedResources! : [],
    parentResources:
      overrides && overrides.hasOwnProperty('parentResources') ? overrides.parentResources! : [],
    resourceType:
      overrides && overrides.hasOwnProperty('resourceType') ? overrides.resourceType! : 'sed',
  };
};

export const buildResourceDetailsList = (
  overrides?: Partial<ResourceDetailsList>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ResourceDetailsList'} & ResourceDetailsList => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ResourceDetailsList');
  return {
    __typename: 'ResourceDetailsList',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildResourceInitFailureEvent = (
  overrides?: Partial<ResourceInitFailureEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ResourceInitFailureEvent'} & ResourceInitFailureEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ResourceInitFailureEvent');
  return {
    __typename: 'ResourceInitFailureEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'quia',
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'mollitia',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'hic',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'dolor',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'perferendis',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'minima',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'quidem',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'qui',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'fuga',
  };
};

export const buildResourceInitStartedEvent = (
  overrides?: Partial<ResourceInitStartedEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ResourceInitStartedEvent'} & ResourceInitStartedEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ResourceInitStartedEvent');
  return {
    __typename: 'ResourceInitStartedEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'et',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'incidunt',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    markerEnd:
      overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'numquam',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'odio',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'et',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'sapiente',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'magni',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'aut',
    timestamp:
      overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'similique',
  };
};

export const buildResourceInitSuccessEvent = (
  overrides?: Partial<ResourceInitSuccessEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ResourceInitSuccessEvent'} & ResourceInitSuccessEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ResourceInitSuccessEvent');
  return {
    __typename: 'ResourceInitSuccessEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'qui',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'fugiat',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'fugiat',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'et',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'ut',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
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
  overrides?: Partial<ResourceNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ResourceNotFoundError'} & ResourceNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ResourceNotFoundError');
  return {
    __typename: 'ResourceNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quo',
    resourceName:
      overrides && overrides.hasOwnProperty('resourceName') ? overrides.resourceName! : 'iure',
  };
};

export const buildResourceRequirement = (
  overrides?: Partial<ResourceRequirement>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ResourceRequirement'} & ResourceRequirement => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ResourceRequirement');
  return {
    __typename: 'ResourceRequirement',
    resourceKey:
      overrides && overrides.hasOwnProperty('resourceKey') ? overrides.resourceKey! : 'pariatur',
  };
};

export const buildResourceSelector = (
  overrides?: Partial<ResourceSelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): ResourceSelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ResourceSelector');
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
  overrides?: Partial<ResumeBackfillSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ResumeBackfillSuccess'} & ResumeBackfillSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ResumeBackfillSuccess');
  return {
    __typename: 'ResumeBackfillSuccess',
    backfillId:
      overrides && overrides.hasOwnProperty('backfillId') ? overrides.backfillId! : 'sint',
  };
};

export const buildRun = (
  overrides?: Partial<Run>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Run'} & Run => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Run');
  return {
    __typename: 'Run',
    assetMaterializations:
      overrides && overrides.hasOwnProperty('assetMaterializations')
        ? overrides.assetMaterializations!
        : [],
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection') ? overrides.assetSelection! : [],
    assets: overrides && overrides.hasOwnProperty('assets') ? overrides.assets! : [],
    canTerminate:
      overrides && overrides.hasOwnProperty('canTerminate') ? overrides.canTerminate! : false,
    capturedLogs:
      overrides && overrides.hasOwnProperty('capturedLogs')
        ? overrides.capturedLogs!
        : relationshipsToOmit.has('CapturedLogs')
        ? ({} as CapturedLogs)
        : buildCapturedLogs({}, relationshipsToOmit),
    computeLogs:
      overrides && overrides.hasOwnProperty('computeLogs')
        ? overrides.computeLogs!
        : relationshipsToOmit.has('ComputeLogs')
        ? ({} as ComputeLogs)
        : buildComputeLogs({}, relationshipsToOmit),
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 7.08,
    eventConnection:
      overrides && overrides.hasOwnProperty('eventConnection')
        ? overrides.eventConnection!
        : relationshipsToOmit.has('EventConnection')
        ? ({} as EventConnection)
        : buildEventConnection({}, relationshipsToOmit),
    executionPlan:
      overrides && overrides.hasOwnProperty('executionPlan')
        ? overrides.executionPlan!
        : relationshipsToOmit.has('ExecutionPlan')
        ? ({} as ExecutionPlan)
        : buildExecutionPlan({}, relationshipsToOmit),
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
        : relationshipsToOmit.has('PipelineReference')
        ? ({} as PipelineReference)
        : buildPipelineReference({}, relationshipsToOmit),
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'enim',
    pipelineSnapshotId:
      overrides && overrides.hasOwnProperty('pipelineSnapshotId')
        ? overrides.pipelineSnapshotId!
        : 'optio',
    repositoryOrigin:
      overrides && overrides.hasOwnProperty('repositoryOrigin')
        ? overrides.repositoryOrigin!
        : relationshipsToOmit.has('RepositoryOrigin')
        ? ({} as RepositoryOrigin)
        : buildRepositoryOrigin({}, relationshipsToOmit),
    resolvedOpSelection:
      overrides && overrides.hasOwnProperty('resolvedOpSelection')
        ? overrides.resolvedOpSelection!
        : [],
    rootRunId: overrides && overrides.hasOwnProperty('rootRunId') ? overrides.rootRunId! : 'fugit',
    runConfig: overrides && overrides.hasOwnProperty('runConfig') ? overrides.runConfig! : 'quas',
    runConfigYaml:
      overrides && overrides.hasOwnProperty('runConfigYaml') ? overrides.runConfigYaml! : 'eveniet',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'fuga',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 2.52,
    stats:
      overrides && overrides.hasOwnProperty('stats')
        ? overrides.stats!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    status:
      overrides && overrides.hasOwnProperty('status') ? overrides.status! : RunStatus.CANCELED,
    stepKeysToExecute:
      overrides && overrides.hasOwnProperty('stepKeysToExecute')
        ? overrides.stepKeysToExecute!
        : [],
    stepStats: overrides && overrides.hasOwnProperty('stepStats') ? overrides.stepStats! : [],
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
    updateTime: overrides && overrides.hasOwnProperty('updateTime') ? overrides.updateTime! : 0,
  };
};

export const buildRunCanceledEvent = (
  overrides?: Partial<RunCanceledEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunCanceledEvent'} & RunCanceledEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunCanceledEvent');
  return {
    __typename: 'RunCanceledEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<RunCancelingEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunCancelingEvent'} & RunCancelingEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunCancelingEvent');
  return {
    __typename: 'RunCancelingEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<RunConfigSchema>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunConfigSchema'} & RunConfigSchema => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunConfigSchema');
  return {
    __typename: 'RunConfigSchema',
    allConfigTypes:
      overrides && overrides.hasOwnProperty('allConfigTypes') ? overrides.allConfigTypes! : [],
    isRunConfigValid:
      overrides && overrides.hasOwnProperty('isRunConfigValid')
        ? overrides.isRunConfigValid!
        : relationshipsToOmit.has('InvalidSubsetError')
        ? ({} as InvalidSubsetError)
        : buildInvalidSubsetError({}, relationshipsToOmit),
    rootConfigType:
      overrides && overrides.hasOwnProperty('rootConfigType')
        ? overrides.rootConfigType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    rootDefaultYaml:
      overrides && overrides.hasOwnProperty('rootDefaultYaml') ? overrides.rootDefaultYaml! : 'cum',
  };
};

export const buildRunConfigValidationInvalid = (
  overrides?: Partial<RunConfigValidationInvalid>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunConfigValidationInvalid'} & RunConfigValidationInvalid => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunConfigValidationInvalid');
  return {
    __typename: 'RunConfigValidationInvalid',
    errors: overrides && overrides.hasOwnProperty('errors') ? overrides.errors! : [],
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'consequatur',
  };
};

export const buildRunConflict = (
  overrides?: Partial<RunConflict>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunConflict'} & RunConflict => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunConflict');
  return {
    __typename: 'RunConflict',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'iste',
  };
};

export const buildRunDequeuedEvent = (
  overrides?: Partial<RunDequeuedEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunDequeuedEvent'} & RunDequeuedEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunDequeuedEvent');
  return {
    __typename: 'RunDequeuedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<RunEnqueuedEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunEnqueuedEvent'} & RunEnqueuedEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunEnqueuedEvent');
  return {
    __typename: 'RunEnqueuedEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<RunEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunEvent'} & RunEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunEvent');
  return {
    __typename: 'RunEvent',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'repudiandae',
  };
};

export const buildRunFailureEvent = (
  overrides?: Partial<RunFailureEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunFailureEvent'} & RunFailureEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunFailureEvent');
  return {
    __typename: 'RunFailureEvent',
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<RunGroup>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunGroup'} & RunGroup => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunGroup');
  return {
    __typename: 'RunGroup',
    rootRunId: overrides && overrides.hasOwnProperty('rootRunId') ? overrides.rootRunId! : 'rem',
    runs: overrides && overrides.hasOwnProperty('runs') ? overrides.runs! : [],
  };
};

export const buildRunGroupNotFoundError = (
  overrides?: Partial<RunGroupNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunGroupNotFoundError'} & RunGroupNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunGroupNotFoundError');
  return {
    __typename: 'RunGroupNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quasi',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'natus',
  };
};

export const buildRunGroups = (
  overrides?: Partial<RunGroups>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunGroups'} & RunGroups => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunGroups');
  return {
    __typename: 'RunGroups',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildRunGroupsOrError = (
  overrides?: Partial<RunGroupsOrError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunGroupsOrError'} & RunGroupsOrError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunGroupsOrError');
  return {
    __typename: 'RunGroupsOrError',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildRunLauncher = (
  overrides?: Partial<RunLauncher>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunLauncher'} & RunLauncher => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunLauncher');
  return {
    __typename: 'RunLauncher',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'iure',
  };
};

export const buildRunMarker = (
  overrides?: Partial<RunMarker>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunMarker'} & RunMarker => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunMarker');
  return {
    __typename: 'RunMarker',
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 5.55,
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 3.49,
  };
};

export const buildRunNotFoundError = (
  overrides?: Partial<RunNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunNotFoundError'} & RunNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunNotFoundError');
  return {
    __typename: 'RunNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'illo',
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'non',
  };
};

export const buildRunRequest = (
  overrides?: Partial<RunRequest>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunRequest'} & RunRequest => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunRequest');
  return {
    __typename: 'RunRequest',
    assetSelection:
      overrides && overrides.hasOwnProperty('assetSelection') ? overrides.assetSelection! : [],
    runConfigYaml:
      overrides && overrides.hasOwnProperty('runConfigYaml') ? overrides.runConfigYaml! : 'ut',
    runKey: overrides && overrides.hasOwnProperty('runKey') ? overrides.runKey! : 'eius',
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildRunStartEvent = (
  overrides?: Partial<RunStartEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunStartEvent'} & RunStartEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunStartEvent');
  return {
    __typename: 'RunStartEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<RunStartingEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunStartingEvent'} & RunStartingEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunStartingEvent');
  return {
    __typename: 'RunStartingEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<RunStatsSnapshot>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunStatsSnapshot'} & RunStatsSnapshot => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunStatsSnapshot');
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
  overrides?: Partial<RunStepStats>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunStepStats'} & RunStepStats => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunStepStats');
  return {
    __typename: 'RunStepStats',
    attempts: overrides && overrides.hasOwnProperty('attempts') ? overrides.attempts! : [],
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 0.92,
    expectationResults:
      overrides && overrides.hasOwnProperty('expectationResults')
        ? overrides.expectationResults!
        : [],
    markers: overrides && overrides.hasOwnProperty('markers') ? overrides.markers! : [],
    materializations:
      overrides && overrides.hasOwnProperty('materializations') ? overrides.materializations! : [],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'repudiandae',
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 7.96,
    status:
      overrides && overrides.hasOwnProperty('status') ? overrides.status! : StepEventStatus.FAILURE,
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'at',
  };
};

export const buildRunSuccessEvent = (
  overrides?: Partial<RunSuccessEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunSuccessEvent'} & RunSuccessEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunSuccessEvent');
  return {
    __typename: 'RunSuccessEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<RunTagKeys>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunTagKeys'} & RunTagKeys => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunTagKeys');
  return {
    __typename: 'RunTagKeys',
    keys: overrides && overrides.hasOwnProperty('keys') ? overrides.keys! : [],
  };
};

export const buildRunTags = (
  overrides?: Partial<RunTags>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RunTags'} & RunTags => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunTags');
  return {
    __typename: 'RunTags',
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
  };
};

export const buildRuns = (
  overrides?: Partial<Runs>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Runs'} & Runs => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Runs');
  return {
    __typename: 'Runs',
    count: overrides && overrides.hasOwnProperty('count') ? overrides.count! : 319,
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildRunsFilter = (
  overrides?: Partial<RunsFilter>,
  _relationshipsToOmit: Set<string> = new Set(),
): RunsFilter => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RunsFilter');
  return {
    createdBefore:
      overrides && overrides.hasOwnProperty('createdBefore') ? overrides.createdBefore! : 2.25,
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'voluptatem',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'voluptas',
    runIds: overrides && overrides.hasOwnProperty('runIds') ? overrides.runIds! : [],
    snapshotId:
      overrides && overrides.hasOwnProperty('snapshotId') ? overrides.snapshotId! : 'quam',
    statuses: overrides && overrides.hasOwnProperty('statuses') ? overrides.statuses! : [],
    tags: overrides && overrides.hasOwnProperty('tags') ? overrides.tags! : [],
    updatedAfter:
      overrides && overrides.hasOwnProperty('updatedAfter') ? overrides.updatedAfter! : 6.85,
  };
};

export const buildRuntimeMismatchConfigError = (
  overrides?: Partial<RuntimeMismatchConfigError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'RuntimeMismatchConfigError'} & RuntimeMismatchConfigError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('RuntimeMismatchConfigError');
  return {
    __typename: 'RuntimeMismatchConfigError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'molestiae',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : [],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : EvaluationErrorReason.FIELDS_NOT_DEFINED,
    stack:
      overrides && overrides.hasOwnProperty('stack')
        ? overrides.stack!
        : relationshipsToOmit.has('EvaluationStack')
        ? ({} as EvaluationStack)
        : buildEvaluationStack({}, relationshipsToOmit),
    valueRep: overrides && overrides.hasOwnProperty('valueRep') ? overrides.valueRep! : 'in',
  };
};

export const buildScalarUnionConfigType = (
  overrides?: Partial<ScalarUnionConfigType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ScalarUnionConfigType'} & ScalarUnionConfigType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ScalarUnionConfigType');
  return {
    __typename: 'ScalarUnionConfigType',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'adipisci',
    isSelector: overrides && overrides.hasOwnProperty('isSelector') ? overrides.isSelector! : false,
    key: overrides && overrides.hasOwnProperty('key') ? overrides.key! : 'quia',
    nonScalarType:
      overrides && overrides.hasOwnProperty('nonScalarType')
        ? overrides.nonScalarType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    nonScalarTypeKey:
      overrides && overrides.hasOwnProperty('nonScalarTypeKey')
        ? overrides.nonScalarTypeKey!
        : 'dolor',
    recursiveConfigTypes:
      overrides && overrides.hasOwnProperty('recursiveConfigTypes')
        ? overrides.recursiveConfigTypes!
        : [],
    scalarType:
      overrides && overrides.hasOwnProperty('scalarType')
        ? overrides.scalarType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
    scalarTypeKey:
      overrides && overrides.hasOwnProperty('scalarTypeKey') ? overrides.scalarTypeKey! : 'esse',
    typeParamKeys:
      overrides && overrides.hasOwnProperty('typeParamKeys') ? overrides.typeParamKeys! : [],
  };
};

export const buildSchedule = (
  overrides?: Partial<Schedule>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Schedule'} & Schedule => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Schedule');
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
        : relationshipsToOmit.has('DryRunInstigationTick')
        ? ({} as DryRunInstigationTick)
        : buildDryRunInstigationTick({}, relationshipsToOmit),
    futureTicks:
      overrides && overrides.hasOwnProperty('futureTicks')
        ? overrides.futureTicks!
        : relationshipsToOmit.has('DryRunInstigationTicks')
        ? ({} as DryRunInstigationTicks)
        : buildDryRunInstigationTicks({}, relationshipsToOmit),
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '71db947a-c94a-4681-979f-7d72688947d9',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'in',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'ut',
    partitionSet:
      overrides && overrides.hasOwnProperty('partitionSet')
        ? overrides.partitionSet!
        : relationshipsToOmit.has('PartitionSet')
        ? ({} as PartitionSet)
        : buildPartitionSet({}, relationshipsToOmit),
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName')
        ? overrides.pipelineName!
        : 'voluptatem',
    potentialTickTimestamps:
      overrides && overrides.hasOwnProperty('potentialTickTimestamps')
        ? overrides.potentialTickTimestamps!
        : [],
    scheduleState:
      overrides && overrides.hasOwnProperty('scheduleState')
        ? overrides.scheduleState!
        : relationshipsToOmit.has('InstigationState')
        ? ({} as InstigationState)
        : buildInstigationState({}, relationshipsToOmit),
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
  };
};

export const buildScheduleData = (
  overrides?: Partial<ScheduleData>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ScheduleData'} & ScheduleData => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ScheduleData');
  return {
    __typename: 'ScheduleData',
    cronSchedule:
      overrides && overrides.hasOwnProperty('cronSchedule') ? overrides.cronSchedule! : 'enim',
    startTimestamp:
      overrides && overrides.hasOwnProperty('startTimestamp') ? overrides.startTimestamp! : 9.43,
  };
};

export const buildScheduleNotFoundError = (
  overrides?: Partial<ScheduleNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ScheduleNotFoundError'} & ScheduleNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ScheduleNotFoundError');
  return {
    __typename: 'ScheduleNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'velit',
    scheduleName:
      overrides && overrides.hasOwnProperty('scheduleName') ? overrides.scheduleName! : 'tempora',
  };
};

export const buildScheduleSelector = (
  overrides?: Partial<ScheduleSelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): ScheduleSelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ScheduleSelector');
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
  overrides?: Partial<ScheduleStateResult>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ScheduleStateResult'} & ScheduleStateResult => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ScheduleStateResult');
  return {
    __typename: 'ScheduleStateResult',
    scheduleState:
      overrides && overrides.hasOwnProperty('scheduleState')
        ? overrides.scheduleState!
        : relationshipsToOmit.has('InstigationState')
        ? ({} as InstigationState)
        : buildInstigationState({}, relationshipsToOmit),
  };
};

export const buildScheduleTick = (
  overrides?: Partial<ScheduleTick>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ScheduleTick'} & ScheduleTick => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ScheduleTick');
  return {
    __typename: 'ScheduleTick',
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : InstigationTickStatus.FAILURE,
    tickId: overrides && overrides.hasOwnProperty('tickId') ? overrides.tickId! : 'fugit',
    tickSpecificData:
      overrides && overrides.hasOwnProperty('tickSpecificData')
        ? overrides.tickSpecificData!
        : relationshipsToOmit.has('ScheduleTickFailureData')
        ? ({} as ScheduleTickFailureData)
        : buildScheduleTickFailureData({}, relationshipsToOmit),
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 2.14,
  };
};

export const buildScheduleTickFailureData = (
  overrides?: Partial<ScheduleTickFailureData>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ScheduleTickFailureData'} & ScheduleTickFailureData => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ScheduleTickFailureData');
  return {
    __typename: 'ScheduleTickFailureData',
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildScheduleTickSuccessData = (
  overrides?: Partial<ScheduleTickSuccessData>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ScheduleTickSuccessData'} & ScheduleTickSuccessData => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ScheduleTickSuccessData');
  return {
    __typename: 'ScheduleTickSuccessData',
    run:
      overrides && overrides.hasOwnProperty('run')
        ? overrides.run!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
  };
};

export const buildScheduler = (
  overrides?: Partial<Scheduler>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Scheduler'} & Scheduler => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Scheduler');
  return {
    __typename: 'Scheduler',
    schedulerClass:
      overrides && overrides.hasOwnProperty('schedulerClass') ? overrides.schedulerClass! : 'qui',
  };
};

export const buildSchedulerNotDefinedError = (
  overrides?: Partial<SchedulerNotDefinedError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SchedulerNotDefinedError'} & SchedulerNotDefinedError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SchedulerNotDefinedError');
  return {
    __typename: 'SchedulerNotDefinedError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'quia',
  };
};

export const buildSchedules = (
  overrides?: Partial<Schedules>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Schedules'} & Schedules => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Schedules');
  return {
    __typename: 'Schedules',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildSelectorTypeConfigError = (
  overrides?: Partial<SelectorTypeConfigError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SelectorTypeConfigError'} & SelectorTypeConfigError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SelectorTypeConfigError');
  return {
    __typename: 'SelectorTypeConfigError',
    incomingFields:
      overrides && overrides.hasOwnProperty('incomingFields') ? overrides.incomingFields! : [],
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'minima',
    path: overrides && overrides.hasOwnProperty('path') ? overrides.path! : [],
    reason:
      overrides && overrides.hasOwnProperty('reason')
        ? overrides.reason!
        : EvaluationErrorReason.FIELDS_NOT_DEFINED,
    stack:
      overrides && overrides.hasOwnProperty('stack')
        ? overrides.stack!
        : relationshipsToOmit.has('EvaluationStack')
        ? ({} as EvaluationStack)
        : buildEvaluationStack({}, relationshipsToOmit),
  };
};

export const buildSensor = (
  overrides?: Partial<Sensor>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Sensor'} & Sensor => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Sensor');
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
        : relationshipsToOmit.has('SensorMetadata')
        ? ({} as SensorMetadata)
        : buildSensorMetadata({}, relationshipsToOmit),
    minIntervalSeconds:
      overrides && overrides.hasOwnProperty('minIntervalSeconds')
        ? overrides.minIntervalSeconds!
        : 6078,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'quibusdam',
    nextTick:
      overrides && overrides.hasOwnProperty('nextTick')
        ? overrides.nextTick!
        : relationshipsToOmit.has('DryRunInstigationTick')
        ? ({} as DryRunInstigationTick)
        : buildDryRunInstigationTick({}, relationshipsToOmit),
    sensorState:
      overrides && overrides.hasOwnProperty('sensorState')
        ? overrides.sensorState!
        : relationshipsToOmit.has('InstigationState')
        ? ({} as InstigationState)
        : buildInstigationState({}, relationshipsToOmit),
    sensorType:
      overrides && overrides.hasOwnProperty('sensorType')
        ? overrides.sensorType!
        : SensorType.ASSET,
    targets: overrides && overrides.hasOwnProperty('targets') ? overrides.targets! : [],
  };
};

export const buildSensorData = (
  overrides?: Partial<SensorData>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SensorData'} & SensorData => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SensorData');
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
  overrides?: Partial<SensorMetadata>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SensorMetadata'} & SensorMetadata => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SensorMetadata');
  return {
    __typename: 'SensorMetadata',
    assetKeys: overrides && overrides.hasOwnProperty('assetKeys') ? overrides.assetKeys! : [],
  };
};

export const buildSensorNotFoundError = (
  overrides?: Partial<SensorNotFoundError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SensorNotFoundError'} & SensorNotFoundError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SensorNotFoundError');
  return {
    __typename: 'SensorNotFoundError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'rerum',
    sensorName:
      overrides && overrides.hasOwnProperty('sensorName') ? overrides.sensorName! : 'corporis',
  };
};

export const buildSensorSelector = (
  overrides?: Partial<SensorSelector>,
  _relationshipsToOmit: Set<string> = new Set(),
): SensorSelector => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SensorSelector');
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
  overrides?: Partial<Sensors>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Sensors'} & Sensors => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Sensors');
  return {
    __typename: 'Sensors',
    results: overrides && overrides.hasOwnProperty('results') ? overrides.results! : [],
  };
};

export const buildSetSensorCursorMutation = (
  overrides?: Partial<SetSensorCursorMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SetSensorCursorMutation'} & SetSensorCursorMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SetSensorCursorMutation');
  return {
    __typename: 'SetSensorCursorMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildShutdownRepositoryLocationMutation = (
  overrides?: Partial<ShutdownRepositoryLocationMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ShutdownRepositoryLocationMutation'} & ShutdownRepositoryLocationMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ShutdownRepositoryLocationMutation');
  return {
    __typename: 'ShutdownRepositoryLocationMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildShutdownRepositoryLocationSuccess = (
  overrides?: Partial<ShutdownRepositoryLocationSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'ShutdownRepositoryLocationSuccess'} & ShutdownRepositoryLocationSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('ShutdownRepositoryLocationSuccess');
  return {
    __typename: 'ShutdownRepositoryLocationSuccess',
    repositoryLocationName:
      overrides && overrides.hasOwnProperty('repositoryLocationName')
        ? overrides.repositoryLocationName!
        : 'assumenda',
  };
};

export const buildSolid = (
  overrides?: Partial<Solid>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Solid'} & Solid => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Solid');
  return {
    __typename: 'Solid',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : relationshipsToOmit.has('ISolidDefinition')
        ? ({} as ISolidDefinition)
        : buildISolidDefinition({}, relationshipsToOmit),
    inputs: overrides && overrides.hasOwnProperty('inputs') ? overrides.inputs! : [],
    isDynamicMapped:
      overrides && overrides.hasOwnProperty('isDynamicMapped') ? overrides.isDynamicMapped! : true,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'rerum',
    outputs: overrides && overrides.hasOwnProperty('outputs') ? overrides.outputs! : [],
  };
};

export const buildSolidContainer = (
  overrides?: Partial<SolidContainer>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SolidContainer'} & SolidContainer => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SolidContainer');
  return {
    __typename: 'SolidContainer',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'velit',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : 'f00f8432-b561-43c1-8978-9fb5fd116ad3',
    modes: overrides && overrides.hasOwnProperty('modes') ? overrides.modes! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'nobis',
    solidHandle:
      overrides && overrides.hasOwnProperty('solidHandle')
        ? overrides.solidHandle!
        : relationshipsToOmit.has('SolidHandle')
        ? ({} as SolidHandle)
        : buildSolidHandle({}, relationshipsToOmit),
    solidHandles:
      overrides && overrides.hasOwnProperty('solidHandles') ? overrides.solidHandles! : [],
    solids: overrides && overrides.hasOwnProperty('solids') ? overrides.solids! : [],
  };
};

export const buildSolidDefinition = (
  overrides?: Partial<SolidDefinition>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SolidDefinition'} & SolidDefinition => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SolidDefinition');
  return {
    __typename: 'SolidDefinition',
    assetNodes: overrides && overrides.hasOwnProperty('assetNodes') ? overrides.assetNodes! : [],
    configField:
      overrides && overrides.hasOwnProperty('configField')
        ? overrides.configField!
        : relationshipsToOmit.has('ConfigTypeField')
        ? ({} as ConfigTypeField)
        : buildConfigTypeField({}, relationshipsToOmit),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'qui',
    inputDefinitions:
      overrides && overrides.hasOwnProperty('inputDefinitions') ? overrides.inputDefinitions! : [],
    metadata: overrides && overrides.hasOwnProperty('metadata') ? overrides.metadata! : [],
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'in',
    outputDefinitions:
      overrides && overrides.hasOwnProperty('outputDefinitions')
        ? overrides.outputDefinitions!
        : [],
    requiredResources:
      overrides && overrides.hasOwnProperty('requiredResources')
        ? overrides.requiredResources!
        : [],
  };
};

export const buildSolidHandle = (
  overrides?: Partial<SolidHandle>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SolidHandle'} & SolidHandle => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SolidHandle');
  return {
    __typename: 'SolidHandle',
    handleID: overrides && overrides.hasOwnProperty('handleID') ? overrides.handleID! : 'iusto',
    parent:
      overrides && overrides.hasOwnProperty('parent')
        ? overrides.parent!
        : relationshipsToOmit.has('SolidHandle')
        ? ({} as SolidHandle)
        : buildSolidHandle({}, relationshipsToOmit),
    solid:
      overrides && overrides.hasOwnProperty('solid')
        ? overrides.solid!
        : relationshipsToOmit.has('Solid')
        ? ({} as Solid)
        : buildSolid({}, relationshipsToOmit),
    stepStats:
      overrides && overrides.hasOwnProperty('stepStats')
        ? overrides.stepStats!
        : relationshipsToOmit.has('SolidStepStatsConnection')
        ? ({} as SolidStepStatsConnection)
        : buildSolidStepStatsConnection({}, relationshipsToOmit),
  };
};

export const buildSolidStepStatsConnection = (
  overrides?: Partial<SolidStepStatsConnection>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SolidStepStatsConnection'} & SolidStepStatsConnection => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SolidStepStatsConnection');
  return {
    __typename: 'SolidStepStatsConnection',
    nodes: overrides && overrides.hasOwnProperty('nodes') ? overrides.nodes! : [],
  };
};

export const buildSolidStepStatusUnavailableError = (
  overrides?: Partial<SolidStepStatusUnavailableError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'SolidStepStatusUnavailableError'} & SolidStepStatusUnavailableError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('SolidStepStatusUnavailableError');
  return {
    __typename: 'SolidStepStatusUnavailableError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'accusantium',
  };
};

export const buildStaleCause = (
  overrides?: Partial<StaleCause>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'StaleCause'} & StaleCause => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StaleCause');
  return {
    __typename: 'StaleCause',
    category:
      overrides && overrides.hasOwnProperty('category')
        ? overrides.category!
        : StaleCauseCategory.CODE,
    dependency:
      overrides && overrides.hasOwnProperty('dependency')
        ? overrides.dependency!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    key:
      overrides && overrides.hasOwnProperty('key')
        ? overrides.key!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    reason: overrides && overrides.hasOwnProperty('reason') ? overrides.reason! : 'et',
  };
};

export const buildStartScheduleMutation = (
  overrides?: Partial<StartScheduleMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'StartScheduleMutation'} & StartScheduleMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StartScheduleMutation');
  return {
    __typename: 'StartScheduleMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildStepEvent = (
  overrides?: Partial<StepEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'StepEvent'} & StepEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StepEvent');
  return {
    __typename: 'StepEvent',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'hic',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'labore',
  };
};

export const buildStepExecution = (
  overrides?: Partial<StepExecution>,
  _relationshipsToOmit: Set<string> = new Set(),
): StepExecution => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StepExecution');
  return {
    marshalledInputs:
      overrides && overrides.hasOwnProperty('marshalledInputs') ? overrides.marshalledInputs! : [],
    marshalledOutputs:
      overrides && overrides.hasOwnProperty('marshalledOutputs')
        ? overrides.marshalledOutputs!
        : [],
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'nihil',
  };
};

export const buildStepExpectationResultEvent = (
  overrides?: Partial<StepExpectationResultEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'StepExpectationResultEvent'} & StepExpectationResultEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StepExpectationResultEvent');
  return {
    __typename: 'StepExpectationResultEvent',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    expectationResult:
      overrides && overrides.hasOwnProperty('expectationResult')
        ? overrides.expectationResult!
        : relationshipsToOmit.has('ExpectationResult')
        ? ({} as ExpectationResult)
        : buildExpectationResult({}, relationshipsToOmit),
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
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
  overrides?: Partial<StepOutputHandle>,
  _relationshipsToOmit: Set<string> = new Set(),
): StepOutputHandle => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StepOutputHandle');
  return {
    outputName: overrides && overrides.hasOwnProperty('outputName') ? overrides.outputName! : 'non',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'et',
  };
};

export const buildStepWorkerStartedEvent = (
  overrides?: Partial<StepWorkerStartedEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'StepWorkerStartedEvent'} & StepWorkerStartedEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StepWorkerStartedEvent');
  return {
    __typename: 'StepWorkerStartedEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'blanditiis',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'voluptatem',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'quod',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'quis',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'veritatis',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    runId: overrides && overrides.hasOwnProperty('runId') ? overrides.runId! : 'nobis',
    solidHandleID:
      overrides && overrides.hasOwnProperty('solidHandleID') ? overrides.solidHandleID! : 'placeat',
    stepKey: overrides && overrides.hasOwnProperty('stepKey') ? overrides.stepKey! : 'minus',
    timestamp: overrides && overrides.hasOwnProperty('timestamp') ? overrides.timestamp! : 'et',
  };
};

export const buildStepWorkerStartingEvent = (
  overrides?: Partial<StepWorkerStartingEvent>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'StepWorkerStartingEvent'} & StepWorkerStartingEvent => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StepWorkerStartingEvent');
  return {
    __typename: 'StepWorkerStartingEvent',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'sint',
    eventType:
      overrides && overrides.hasOwnProperty('eventType')
        ? overrides.eventType!
        : DagsterEventType.ALERT_FAILURE,
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'cupiditate',
    level: overrides && overrides.hasOwnProperty('level') ? overrides.level! : LogLevel.CRITICAL,
    markerEnd: overrides && overrides.hasOwnProperty('markerEnd') ? overrides.markerEnd! : 'qui',
    markerStart:
      overrides && overrides.hasOwnProperty('markerStart') ? overrides.markerStart! : 'et',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'deserunt',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
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
  overrides?: Partial<StopRunningScheduleMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'StopRunningScheduleMutation'} & StopRunningScheduleMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StopRunningScheduleMutation');
  return {
    __typename: 'StopRunningScheduleMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildStopSensorMutation = (
  overrides?: Partial<StopSensorMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'StopSensorMutation'} & StopSensorMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StopSensorMutation');
  return {
    __typename: 'StopSensorMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildStopSensorMutationResult = (
  overrides?: Partial<StopSensorMutationResult>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'StopSensorMutationResult'} & StopSensorMutationResult => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('StopSensorMutationResult');
  return {
    __typename: 'StopSensorMutationResult',
    instigationState:
      overrides && overrides.hasOwnProperty('instigationState')
        ? overrides.instigationState!
        : relationshipsToOmit.has('InstigationState')
        ? ({} as InstigationState)
        : buildInstigationState({}, relationshipsToOmit),
  };
};

export const buildTable = (
  overrides?: Partial<Table>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Table'} & Table => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Table');
  return {
    __typename: 'Table',
    records: overrides && overrides.hasOwnProperty('records') ? overrides.records! : [],
    schema:
      overrides && overrides.hasOwnProperty('schema')
        ? overrides.schema!
        : relationshipsToOmit.has('TableSchema')
        ? ({} as TableSchema)
        : buildTableSchema({}, relationshipsToOmit),
  };
};

export const buildTableColumn = (
  overrides?: Partial<TableColumn>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TableColumn'} & TableColumn => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TableColumn');
  return {
    __typename: 'TableColumn',
    constraints:
      overrides && overrides.hasOwnProperty('constraints')
        ? overrides.constraints!
        : relationshipsToOmit.has('TableColumnConstraints')
        ? ({} as TableColumnConstraints)
        : buildTableColumnConstraints({}, relationshipsToOmit),
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'illum',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'explicabo',
    type: overrides && overrides.hasOwnProperty('type') ? overrides.type! : 'a',
  };
};

export const buildTableColumnConstraints = (
  overrides?: Partial<TableColumnConstraints>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TableColumnConstraints'} & TableColumnConstraints => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TableColumnConstraints');
  return {
    __typename: 'TableColumnConstraints',
    nullable: overrides && overrides.hasOwnProperty('nullable') ? overrides.nullable! : true,
    other: overrides && overrides.hasOwnProperty('other') ? overrides.other! : [],
    unique: overrides && overrides.hasOwnProperty('unique') ? overrides.unique! : false,
  };
};

export const buildTableConstraints = (
  overrides?: Partial<TableConstraints>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TableConstraints'} & TableConstraints => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TableConstraints');
  return {
    __typename: 'TableConstraints',
    other: overrides && overrides.hasOwnProperty('other') ? overrides.other! : [],
  };
};

export const buildTableMetadataEntry = (
  overrides?: Partial<TableMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TableMetadataEntry'} & TableMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TableMetadataEntry');
  return {
    __typename: 'TableMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'sed',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'quia',
    table:
      overrides && overrides.hasOwnProperty('table')
        ? overrides.table!
        : relationshipsToOmit.has('Table')
        ? ({} as Table)
        : buildTable({}, relationshipsToOmit),
  };
};

export const buildTableSchema = (
  overrides?: Partial<TableSchema>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TableSchema'} & TableSchema => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TableSchema');
  return {
    __typename: 'TableSchema',
    columns: overrides && overrides.hasOwnProperty('columns') ? overrides.columns! : [],
    constraints:
      overrides && overrides.hasOwnProperty('constraints')
        ? overrides.constraints!
        : relationshipsToOmit.has('TableConstraints')
        ? ({} as TableConstraints)
        : buildTableConstraints({}, relationshipsToOmit),
  };
};

export const buildTableSchemaMetadataEntry = (
  overrides?: Partial<TableSchemaMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TableSchemaMetadataEntry'} & TableSchemaMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TableSchemaMetadataEntry');
  return {
    __typename: 'TableSchemaMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'itaque',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'libero',
    schema:
      overrides && overrides.hasOwnProperty('schema')
        ? overrides.schema!
        : relationshipsToOmit.has('TableSchema')
        ? ({} as TableSchema)
        : buildTableSchema({}, relationshipsToOmit),
  };
};

export const buildTarget = (
  overrides?: Partial<Target>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Target'} & Target => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Target');
  return {
    __typename: 'Target',
    mode: overrides && overrides.hasOwnProperty('mode') ? overrides.mode! : 'porro',
    pipelineName:
      overrides && overrides.hasOwnProperty('pipelineName') ? overrides.pipelineName! : 'aut',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
  };
};

export const buildTerminatePipelineExecutionFailure = (
  overrides?: Partial<TerminatePipelineExecutionFailure>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TerminatePipelineExecutionFailure'} & TerminatePipelineExecutionFailure => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TerminatePipelineExecutionFailure');
  return {
    __typename: 'TerminatePipelineExecutionFailure',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'vero',
    run:
      overrides && overrides.hasOwnProperty('run')
        ? overrides.run!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
  };
};

export const buildTerminatePipelineExecutionSuccess = (
  overrides?: Partial<TerminatePipelineExecutionSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TerminatePipelineExecutionSuccess'} & TerminatePipelineExecutionSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TerminatePipelineExecutionSuccess');
  return {
    __typename: 'TerminatePipelineExecutionSuccess',
    run:
      overrides && overrides.hasOwnProperty('run')
        ? overrides.run!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
  };
};

export const buildTerminateRunFailure = (
  overrides?: Partial<TerminateRunFailure>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TerminateRunFailure'} & TerminateRunFailure => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TerminateRunFailure');
  return {
    __typename: 'TerminateRunFailure',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'sit',
    run:
      overrides && overrides.hasOwnProperty('run')
        ? overrides.run!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
  };
};

export const buildTerminateRunMutation = (
  overrides?: Partial<TerminateRunMutation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TerminateRunMutation'} & TerminateRunMutation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TerminateRunMutation');
  return {
    __typename: 'TerminateRunMutation',
    Output:
      overrides && overrides.hasOwnProperty('Output')
        ? overrides.Output!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
  };
};

export const buildTerminateRunSuccess = (
  overrides?: Partial<TerminateRunSuccess>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TerminateRunSuccess'} & TerminateRunSuccess => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TerminateRunSuccess');
  return {
    __typename: 'TerminateRunSuccess',
    run:
      overrides && overrides.hasOwnProperty('run')
        ? overrides.run!
        : relationshipsToOmit.has('Run')
        ? ({} as Run)
        : buildRun({}, relationshipsToOmit),
  };
};

export const buildTestFields = (
  overrides?: Partial<TestFields>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TestFields'} & TestFields => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TestFields');
  return {
    __typename: 'TestFields',
    alwaysException:
      overrides && overrides.hasOwnProperty('alwaysException')
        ? overrides.alwaysException!
        : 'quibusdam',
  };
};

export const buildTextMetadataEntry = (
  overrides?: Partial<TextMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TextMetadataEntry'} & TextMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TextMetadataEntry');
  return {
    __typename: 'TextMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'illum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'quae',
    text: overrides && overrides.hasOwnProperty('text') ? overrides.text! : 'dignissimos',
  };
};

export const buildTickEvaluation = (
  overrides?: Partial<TickEvaluation>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TickEvaluation'} & TickEvaluation => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TickEvaluation');
  return {
    __typename: 'TickEvaluation',
    cursor: overrides && overrides.hasOwnProperty('cursor') ? overrides.cursor! : 'est',
    dynamicPartitionsRequests:
      overrides && overrides.hasOwnProperty('dynamicPartitionsRequests')
        ? overrides.dynamicPartitionsRequests!
        : [],
    error:
      overrides && overrides.hasOwnProperty('error')
        ? overrides.error!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    runRequests: overrides && overrides.hasOwnProperty('runRequests') ? overrides.runRequests! : [],
    skipReason:
      overrides && overrides.hasOwnProperty('skipReason') ? overrides.skipReason! : 'dicta',
  };
};

export const buildTimePartitionRangeStatus = (
  overrides?: Partial<TimePartitionRangeStatus>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TimePartitionRangeStatus'} & TimePartitionRangeStatus => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TimePartitionRangeStatus');
  return {
    __typename: 'TimePartitionRangeStatus',
    endKey: overrides && overrides.hasOwnProperty('endKey') ? overrides.endKey! : 'vero',
    endTime: overrides && overrides.hasOwnProperty('endTime') ? overrides.endTime! : 9.24,
    startKey: overrides && overrides.hasOwnProperty('startKey') ? overrides.startKey! : 'totam',
    startTime: overrides && overrides.hasOwnProperty('startTime') ? overrides.startTime! : 0.57,
    status:
      overrides && overrides.hasOwnProperty('status')
        ? overrides.status!
        : PartitionRangeStatus.FAILED,
  };
};

export const buildTimePartitionStatuses = (
  overrides?: Partial<TimePartitionStatuses>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TimePartitionStatuses'} & TimePartitionStatuses => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TimePartitionStatuses');
  return {
    __typename: 'TimePartitionStatuses',
    ranges: overrides && overrides.hasOwnProperty('ranges') ? overrides.ranges! : [],
  };
};

export const buildTypeCheck = (
  overrides?: Partial<TypeCheck>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'TypeCheck'} & TypeCheck => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('TypeCheck');
  return {
    __typename: 'TypeCheck',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'odio',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'accusamus',
    metadataEntries:
      overrides && overrides.hasOwnProperty('metadataEntries') ? overrides.metadataEntries! : [],
    success: overrides && overrides.hasOwnProperty('success') ? overrides.success! : true,
  };
};

export const buildUnauthorizedError = (
  overrides?: Partial<UnauthorizedError>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'UnauthorizedError'} & UnauthorizedError => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('UnauthorizedError');
  return {
    __typename: 'UnauthorizedError',
    message: overrides && overrides.hasOwnProperty('message') ? overrides.message! : 'porro',
  };
};

export const buildUnknownPipeline = (
  overrides?: Partial<UnknownPipeline>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'UnknownPipeline'} & UnknownPipeline => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('UnknownPipeline');
  return {
    __typename: 'UnknownPipeline',
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'dicta',
    solidSelection:
      overrides && overrides.hasOwnProperty('solidSelection') ? overrides.solidSelection! : [],
  };
};

export const buildUnpartitionedAssetStatus = (
  overrides?: Partial<UnpartitionedAssetStatus>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'UnpartitionedAssetStatus'} & UnpartitionedAssetStatus => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('UnpartitionedAssetStatus');
  return {
    __typename: 'UnpartitionedAssetStatus',
    assetKey:
      overrides && overrides.hasOwnProperty('assetKey')
        ? overrides.assetKey!
        : relationshipsToOmit.has('AssetKey')
        ? ({} as AssetKey)
        : buildAssetKey({}, relationshipsToOmit),
    failed: overrides && overrides.hasOwnProperty('failed') ? overrides.failed! : true,
    inProgress: overrides && overrides.hasOwnProperty('inProgress') ? overrides.inProgress! : false,
    materialized:
      overrides && overrides.hasOwnProperty('materialized') ? overrides.materialized! : false,
  };
};

export const buildUrlMetadataEntry = (
  overrides?: Partial<UrlMetadataEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'UrlMetadataEntry'} & UrlMetadataEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('UrlMetadataEntry');
  return {
    __typename: 'UrlMetadataEntry',
    description:
      overrides && overrides.hasOwnProperty('description') ? overrides.description! : 'cum',
    label: overrides && overrides.hasOwnProperty('label') ? overrides.label! : 'ut',
    url: overrides && overrides.hasOwnProperty('url') ? overrides.url! : 'optio',
  };
};

export const buildUsedSolid = (
  overrides?: Partial<UsedSolid>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'UsedSolid'} & UsedSolid => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('UsedSolid');
  return {
    __typename: 'UsedSolid',
    definition:
      overrides && overrides.hasOwnProperty('definition')
        ? overrides.definition!
        : relationshipsToOmit.has('ISolidDefinition')
        ? ({} as ISolidDefinition)
        : buildISolidDefinition({}, relationshipsToOmit),
    invocations: overrides && overrides.hasOwnProperty('invocations') ? overrides.invocations! : [],
  };
};

export const buildWorkspace = (
  overrides?: Partial<Workspace>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'Workspace'} & Workspace => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('Workspace');
  return {
    __typename: 'Workspace',
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'id',
    locationEntries:
      overrides && overrides.hasOwnProperty('locationEntries') ? overrides.locationEntries! : [],
  };
};

export const buildWorkspaceLocationEntry = (
  overrides?: Partial<WorkspaceLocationEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'WorkspaceLocationEntry'} & WorkspaceLocationEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('WorkspaceLocationEntry');
  return {
    __typename: 'WorkspaceLocationEntry',
    displayMetadata:
      overrides && overrides.hasOwnProperty('displayMetadata') ? overrides.displayMetadata! : [],
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '6b0adcaa-46a3-49a8-98bb-9f5288e9711a',
    loadStatus:
      overrides && overrides.hasOwnProperty('loadStatus')
        ? overrides.loadStatus!
        : RepositoryLocationLoadStatus.LOADED,
    locationOrLoadError:
      overrides && overrides.hasOwnProperty('locationOrLoadError')
        ? overrides.locationOrLoadError!
        : relationshipsToOmit.has('PythonError')
        ? ({} as PythonError)
        : buildPythonError({}, relationshipsToOmit),
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'sint',
    permissions: overrides && overrides.hasOwnProperty('permissions') ? overrides.permissions! : [],
    updatedTimestamp:
      overrides && overrides.hasOwnProperty('updatedTimestamp')
        ? overrides.updatedTimestamp!
        : 2.68,
  };
};

export const buildWorkspaceLocationStatusEntries = (
  overrides?: Partial<WorkspaceLocationStatusEntries>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'WorkspaceLocationStatusEntries'} & WorkspaceLocationStatusEntries => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('WorkspaceLocationStatusEntries');
  return {
    __typename: 'WorkspaceLocationStatusEntries',
    entries: overrides && overrides.hasOwnProperty('entries') ? overrides.entries! : [],
  };
};

export const buildWorkspaceLocationStatusEntry = (
  overrides?: Partial<WorkspaceLocationStatusEntry>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'WorkspaceLocationStatusEntry'} & WorkspaceLocationStatusEntry => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('WorkspaceLocationStatusEntry');
  return {
    __typename: 'WorkspaceLocationStatusEntry',
    id:
      overrides && overrides.hasOwnProperty('id')
        ? overrides.id!
        : '485aa087-be75-4f2b-a1bc-be732927a8cc',
    loadStatus:
      overrides && overrides.hasOwnProperty('loadStatus')
        ? overrides.loadStatus!
        : RepositoryLocationLoadStatus.LOADED,
    name: overrides && overrides.hasOwnProperty('name') ? overrides.name! : 'corporis',
    updateTimestamp:
      overrides && overrides.hasOwnProperty('updateTimestamp') ? overrides.updateTimestamp! : 7.09,
  };
};

export const buildWrappingConfigType = (
  overrides?: Partial<WrappingConfigType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'WrappingConfigType'} & WrappingConfigType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('WrappingConfigType');
  return {
    __typename: 'WrappingConfigType',
    ofType:
      overrides && overrides.hasOwnProperty('ofType')
        ? overrides.ofType!
        : relationshipsToOmit.has('ConfigType')
        ? ({} as ConfigType)
        : buildConfigType({}, relationshipsToOmit),
  };
};

export const buildWrappingDagsterType = (
  overrides?: Partial<WrappingDagsterType>,
  _relationshipsToOmit: Set<string> = new Set(),
): {__typename: 'WrappingDagsterType'} & WrappingDagsterType => {
  const relationshipsToOmit: Set<string> = new Set(_relationshipsToOmit);
  relationshipsToOmit.add('WrappingDagsterType');
  return {
    __typename: 'WrappingDagsterType',
    ofType:
      overrides && overrides.hasOwnProperty('ofType')
        ? overrides.ofType!
        : relationshipsToOmit.has('DagsterType')
        ? ({} as DagsterType)
        : buildDagsterType({}, relationshipsToOmit),
  };
};
