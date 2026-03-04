// Generated GraphQL types, do not edit manually.

import {AssetCheckCanExecuteIndividually} from './types';
import {AssetCheckExecutionResolvedStatus} from './types';
import {AssetCheckPartitionRangeStatus} from './types';
import {AssetCheckSeverity} from './types';
import {AssetConditionEvaluationStatus} from './types';
import {AssetEventHistoryEventTypeSelector} from './types';
import {AssetEventType} from './types';
import {AssetHealthStatus} from './types';
import {AssetMaterializationFailureReason} from './types';
import {AssetMaterializationFailureType} from './types';
import {AutoMaterializeDecisionType} from './types';
import {AutoMaterializePolicyType} from './types';
import {BackfillPolicyType} from './types';
import {BulkActionStatus} from './types';
import {ChangeReason} from './types';
import {ConfiguredValueType} from './types';
import {DagsterEventType} from './types';
import {DefinitionsSource} from './types';
import {DefsStateManagementType} from './types';
import {DynamicPartitionsRequestType} from './types';
import {EnvVarConsumerType} from './types';
import {ErrorSource} from './types';
import {EvaluationErrorReason} from './types';
import {InstigationStatus} from './types';
import {InstigationTickStatus} from './types';
import {InstigationType} from './types';
import {LocationStateChangeEventType} from './types';
import {LogLevel} from './types';
import {NestedResourceType} from './types';
import {ObjectStoreOperationType} from './types';
import {PartitionDefinitionType} from './types';
import {PartitionRangeStatus} from './types';
import {ReexecutionStrategy} from './types';
import {RepositoryLocationLoadStatus} from './types';
import {RunStatus} from './types';
import {RunsFeedView} from './types';
import {ScheduleStatus} from './types';
import {SensorType} from './types';
import {StaleCauseCategory} from './types';
import {StaleStatus} from './types';
import {StepEventStatus} from './types';
import {StepKind} from './types';
import {TerminateRunPolicy} from './types';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & {[SubKey in K]?: Maybe<T[SubKey]>};
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & {[SubKey in K]: Maybe<T[SubKey]>};
export type MakeEmpty<T extends {[key: string]: unknown}, K extends keyof T> = {[_ in K]?: never};
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: {input: string; output: string};
  String: {input: string; output: string};
  Boolean: {input: boolean; output: boolean};
  Int: {input: number; output: number};
  Float: {input: number; output: number};
  GenericScalar: {input: any; output: any};
  JSONString: {input: any; output: any};
  RunConfigData: {input: any; output: any};
};

export type AddDynamicPartitionResult =
  | AddDynamicPartitionSuccess
  | DuplicateDynamicPartitionError
  | PythonError
  | UnauthorizedError;

export type AddDynamicPartitionSuccess = {
  __typename: 'AddDynamicPartitionSuccess';
  partitionKey: Scalars['String']['output'];
  partitionsDefName: Scalars['String']['output'];
};

export type AlertFailureEvent = MessageEvent &
  RunEvent & {
    __typename: 'AlertFailureEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type AlertStartEvent = MessageEvent &
  RunEvent & {
    __typename: 'AlertStartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type AlertSuccessEvent = MessageEvent &
  RunEvent & {
    __typename: 'AlertSuccessEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ArrayConfigType = ConfigType &
  WrappingConfigType & {
    __typename: 'ArrayConfigType';
    description: Maybe<Scalars['String']['output']>;
    isSelector: Scalars['Boolean']['output'];
    key: Scalars['String']['output'];
    ofType:
      | ArrayConfigType
      | CompositeConfigType
      | EnumConfigType
      | MapConfigType
      | NullableConfigType
      | RegularConfigType
      | ScalarUnionConfigType;
    recursiveConfigTypes: Array<
      | ArrayConfigType
      | CompositeConfigType
      | EnumConfigType
      | MapConfigType
      | NullableConfigType
      | RegularConfigType
      | ScalarUnionConfigType
    >;
    typeParamKeys: Array<Scalars['String']['output']>;
  };

export type Asset = {
  __typename: 'Asset';
  assetEventHistory: AssetResultEventHistoryConnection;
  assetHealth: Maybe<AssetHealth>;
  assetMaterializations: Array<MaterializationEvent>;
  assetObservations: Array<ObservationEvent>;
  definition: Maybe<AssetNode>;
  freshnessStatusChangedTimestamp: Maybe<Scalars['Float']['output']>;
  hasDefinitionOrRecord: Scalars['Boolean']['output'];
  id: Scalars['String']['output'];
  key: AssetKey;
  latestEventSortKey: Maybe<Scalars['ID']['output']>;
  latestFailedToMaterializeTimestamp: Maybe<Scalars['Float']['output']>;
  latestMaterializationTimestamp: Maybe<Scalars['Float']['output']>;
};

export type AssetAssetEventHistoryArgs = {
  afterTimestampMillis?: InputMaybe<Scalars['String']['input']>;
  beforeTimestampMillis?: InputMaybe<Scalars['String']['input']>;
  cursor?: InputMaybe<Scalars['String']['input']>;
  eventTypeSelectors: Array<AssetEventHistoryEventTypeSelector>;
  limit: Scalars['Int']['input'];
  partitions?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type AssetAssetMaterializationsArgs = {
  afterTimestampMillis?: InputMaybe<Scalars['String']['input']>;
  beforeTimestampMillis?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  partitions?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type AssetAssetObservationsArgs = {
  afterTimestampMillis?: InputMaybe<Scalars['String']['input']>;
  beforeTimestampMillis?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  partitions?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type AssetBackfillData = {
  __typename: 'AssetBackfillData';
  assetBackfillStatuses: Array<AssetBackfillStatus>;
  rootTargetedPartitions: Maybe<AssetBackfillTargetPartitions>;
};

export type AssetBackfillPreviewParams = {
  assetSelection: Array<AssetKeyInput>;
  partitionNames: Array<Scalars['String']['input']>;
};

export type AssetBackfillStatus = AssetPartitionsStatusCounts | UnpartitionedAssetStatus;

export type AssetBackfillTargetPartitions = {
  __typename: 'AssetBackfillTargetPartitions';
  partitionKeys: Maybe<Array<Scalars['String']['output']>>;
  ranges: Maybe<Array<PartitionKeyRange>>;
};

export type AssetCheck = {
  __typename: 'AssetCheck';
  additionalAssetKeys: Array<AssetKey>;
  assetKey: AssetKey;
  automationCondition: Maybe<AutomationCondition>;
  blocking: Scalars['Boolean']['output'];
  canExecuteIndividually: AssetCheckCanExecuteIndividually;
  description: Maybe<Scalars['String']['output']>;
  executionForLatestMaterialization: Maybe<AssetCheckExecution>;
  jobNames: Array<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  partitionDefinition: Maybe<PartitionDefinition>;
  partitionKeysByDimension: Array<DimensionPartitionKeys>;
  partitionStatuses: Maybe<AssetCheckPartitionStatuses>;
};

export type AssetCheckPartitionKeysByDimensionArgs = {
  endIdx?: InputMaybe<Scalars['Int']['input']>;
  startIdx?: InputMaybe<Scalars['Int']['input']>;
};

export {AssetCheckCanExecuteIndividually};

export type AssetCheckDefaultPartitionStatuses = {
  __typename: 'AssetCheckDefaultPartitionStatuses';
  executionFailedPartitions: Array<Scalars['String']['output']>;
  failedPartitions: Array<Scalars['String']['output']>;
  inProgressPartitions: Array<Scalars['String']['output']>;
  skippedPartitions: Array<Scalars['String']['output']>;
  succeededPartitions: Array<Scalars['String']['output']>;
};

export type AssetCheckEvaluation = {
  __typename: 'AssetCheckEvaluation';
  assetKey: AssetKey;
  checkName: Scalars['String']['output'];
  description: Maybe<Scalars['String']['output']>;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  partition: Maybe<Scalars['String']['output']>;
  severity: AssetCheckSeverity;
  success: Scalars['Boolean']['output'];
  targetMaterialization: Maybe<AssetCheckEvaluationTargetMaterializationData>;
  timestamp: Scalars['Float']['output'];
};

export type AssetCheckEvaluationEvent = MessageEvent &
  StepEvent & {
    __typename: 'AssetCheckEvaluationEvent';
    evaluation: AssetCheckEvaluation;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type AssetCheckEvaluationPlannedEvent = MessageEvent &
  StepEvent & {
    __typename: 'AssetCheckEvaluationPlannedEvent';
    assetKey: AssetKey;
    checkName: Scalars['String']['output'];
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type AssetCheckEvaluationTargetMaterializationData = {
  __typename: 'AssetCheckEvaluationTargetMaterializationData';
  runId: Scalars['String']['output'];
  storageId: Scalars['ID']['output'];
  timestamp: Scalars['Float']['output'];
};

export type AssetCheckExecution = {
  __typename: 'AssetCheckExecution';
  evaluation: Maybe<AssetCheckEvaluation>;
  id: Scalars['String']['output'];
  partition: Maybe<Scalars['String']['output']>;
  run: Maybe<Run>;
  runId: Scalars['String']['output'];
  status: AssetCheckExecutionResolvedStatus;
  stepKey: Maybe<Scalars['String']['output']>;
  timestamp: Scalars['Float']['output'];
};

export {AssetCheckExecutionResolvedStatus};

export type AssetCheckHandleInput = {
  assetKey: AssetKeyInput;
  name: Scalars['String']['input'];
};

export type AssetCheckMultiPartitionRangeStatuses = {
  __typename: 'AssetCheckMultiPartitionRangeStatuses';
  primaryDimEndKey: Scalars['String']['output'];
  primaryDimEndTime: Maybe<Scalars['Float']['output']>;
  primaryDimStartKey: Scalars['String']['output'];
  primaryDimStartTime: Maybe<Scalars['Float']['output']>;
  secondaryDim: AssetCheckPartitionStatus1D;
};

export type AssetCheckMultiPartitionStatuses = {
  __typename: 'AssetCheckMultiPartitionStatuses';
  primaryDimensionName: Scalars['String']['output'];
  ranges: Array<AssetCheckMultiPartitionRangeStatuses>;
};

export type AssetCheckNeedsAgentUpgradeError = Error & {
  __typename: 'AssetCheckNeedsAgentUpgradeError';
  message: Scalars['String']['output'];
};

export type AssetCheckNeedsMigrationError = Error & {
  __typename: 'AssetCheckNeedsMigrationError';
  message: Scalars['String']['output'];
};

export type AssetCheckNeedsUserCodeUpgrade = Error & {
  __typename: 'AssetCheckNeedsUserCodeUpgrade';
  message: Scalars['String']['output'];
};

export type AssetCheckNotFoundError = Error & {
  __typename: 'AssetCheckNotFoundError';
  message: Scalars['String']['output'];
};

export type AssetCheckOrError =
  | AssetCheck
  | AssetCheckNeedsAgentUpgradeError
  | AssetCheckNeedsMigrationError
  | AssetCheckNeedsUserCodeUpgrade
  | AssetCheckNotFoundError;

export {AssetCheckPartitionRangeStatus};

export type AssetCheckPartitionStatus1D =
  | AssetCheckDefaultPartitionStatuses
  | AssetCheckTimePartitionStatuses;

export type AssetCheckPartitionStatuses =
  | AssetCheckDefaultPartitionStatuses
  | AssetCheckMultiPartitionStatuses
  | AssetCheckTimePartitionStatuses;

export {AssetCheckSeverity};

export type AssetCheckTimePartitionRangeStatus = {
  __typename: 'AssetCheckTimePartitionRangeStatus';
  endKey: Scalars['String']['output'];
  endTime: Scalars['Float']['output'];
  startKey: Scalars['String']['output'];
  startTime: Scalars['Float']['output'];
  status: AssetCheckPartitionRangeStatus;
};

export type AssetCheckTimePartitionStatuses = {
  __typename: 'AssetCheckTimePartitionStatuses';
  ranges: Array<AssetCheckTimePartitionRangeStatus>;
};

export type AssetCheckhandle = {
  __typename: 'AssetCheckhandle';
  assetKey: AssetKey;
  name: Scalars['String']['output'];
};

export type AssetChecks = {
  __typename: 'AssetChecks';
  checks: Array<AssetCheck>;
};

export type AssetChecksOrError =
  | AssetCheckNeedsAgentUpgradeError
  | AssetCheckNeedsMigrationError
  | AssetCheckNeedsUserCodeUpgrade
  | AssetChecks;

export type AssetConditionEvaluation = {
  __typename: 'AssetConditionEvaluation';
  evaluationNodes: Array<AssetConditionEvaluationNode>;
  rootUniqueId: Scalars['String']['output'];
};

export type AssetConditionEvaluationNode =
  | PartitionedAssetConditionEvaluationNode
  | SpecificPartitionAssetConditionEvaluationNode
  | UnpartitionedAssetConditionEvaluationNode;

export type AssetConditionEvaluationRecord = {
  __typename: 'AssetConditionEvaluationRecord';
  assetKey: Maybe<AssetKey>;
  endTimestamp: Maybe<Scalars['Float']['output']>;
  entityKey: EntityKey;
  evaluation: AssetConditionEvaluation;
  evaluationId: Scalars['ID']['output'];
  evaluationNodes: Array<AutomationConditionEvaluationNode>;
  id: Scalars['ID']['output'];
  isLegacy: Scalars['Boolean']['output'];
  numRequested: Maybe<Scalars['Int']['output']>;
  rootUniqueId: Scalars['String']['output'];
  runIds: Array<Scalars['String']['output']>;
  startTimestamp: Maybe<Scalars['Float']['output']>;
  timestamp: Scalars['Float']['output'];
};

export type AssetConditionEvaluationRecords = {
  __typename: 'AssetConditionEvaluationRecords';
  records: Array<AssetConditionEvaluationRecord>;
};

export type AssetConditionEvaluationRecordsOrError =
  | AssetConditionEvaluationRecords
  | AutoMaterializeAssetEvaluationNeedsMigrationError;

export {AssetConditionEvaluationStatus};

export type AssetConnection = {
  __typename: 'AssetConnection';
  cursor: Maybe<Scalars['String']['output']>;
  nodes: Array<Asset>;
};

export type AssetDependency = {
  __typename: 'AssetDependency';
  asset: AssetNode;
  partitionMapping: Maybe<PartitionMapping>;
};

export {AssetEventHistoryEventTypeSelector};

export {AssetEventType};

export type AssetFreshnessInfo = {
  __typename: 'AssetFreshnessInfo';
  currentLagMinutes: Maybe<Scalars['Float']['output']>;
  currentMinutesLate: Maybe<Scalars['Float']['output']>;
  latestMaterializationMinutesLate: Maybe<Scalars['Float']['output']>;
};

export type AssetGroup = {
  __typename: 'AssetGroup';
  assetKeys: Array<AssetKey>;
  groupName: Scalars['String']['output'];
  id: Scalars['String']['output'];
};

export type AssetGroupSelector = {
  groupName: Scalars['String']['input'];
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
};

export type AssetHealth = {
  __typename: 'AssetHealth';
  assetChecksStatus: AssetHealthStatus;
  assetChecksStatusMetadata: Maybe<AssetHealthCheckMeta>;
  assetHealth: AssetHealthStatus;
  freshnessStatus: AssetHealthStatus;
  freshnessStatusMetadata: Maybe<AssetHealthFreshnessMeta>;
  materializationStatus: AssetHealthStatus;
  materializationStatusMetadata: Maybe<AssetHealthMaterializationMeta>;
};

export type AssetHealthCheckDegradedMeta = {
  __typename: 'AssetHealthCheckDegradedMeta';
  numFailedChecks: Scalars['Int']['output'];
  numWarningChecks: Scalars['Int']['output'];
  totalNumChecks: Scalars['Int']['output'];
};

export type AssetHealthCheckMeta =
  | AssetHealthCheckDegradedMeta
  | AssetHealthCheckUnknownMeta
  | AssetHealthCheckWarningMeta;

export type AssetHealthCheckUnknownMeta = {
  __typename: 'AssetHealthCheckUnknownMeta';
  numNotExecutedChecks: Scalars['Int']['output'];
  totalNumChecks: Scalars['Int']['output'];
};

export type AssetHealthCheckWarningMeta = {
  __typename: 'AssetHealthCheckWarningMeta';
  numWarningChecks: Scalars['Int']['output'];
  totalNumChecks: Scalars['Int']['output'];
};

export type AssetHealthFreshnessMeta = {
  __typename: 'AssetHealthFreshnessMeta';
  lastMaterializedTimestamp: Maybe<Scalars['Float']['output']>;
};

export type AssetHealthMaterializationDegradedNotPartitionedMeta = {
  __typename: 'AssetHealthMaterializationDegradedNotPartitionedMeta';
  failedRunId: Maybe<Scalars['String']['output']>;
};

export type AssetHealthMaterializationDegradedPartitionedMeta = {
  __typename: 'AssetHealthMaterializationDegradedPartitionedMeta';
  latestFailedRunId: Maybe<Scalars['String']['output']>;
  latestRunId: Maybe<Scalars['String']['output']>;
  numFailedPartitions: Scalars['Int']['output'];
  numMissingPartitions: Scalars['Int']['output'];
  totalNumPartitions: Scalars['Int']['output'];
};

export type AssetHealthMaterializationHealthyPartitionedMeta = {
  __typename: 'AssetHealthMaterializationHealthyPartitionedMeta';
  latestRunId: Maybe<Scalars['String']['output']>;
  numMissingPartitions: Scalars['Int']['output'];
  totalNumPartitions: Scalars['Int']['output'];
};

export type AssetHealthMaterializationMeta =
  | AssetHealthMaterializationDegradedNotPartitionedMeta
  | AssetHealthMaterializationDegradedPartitionedMeta
  | AssetHealthMaterializationHealthyPartitionedMeta;

export {AssetHealthStatus};

export type AssetKey = {
  __typename: 'AssetKey';
  path: Array<Scalars['String']['output']>;
};

export type AssetKeyInput = {
  path: Array<Scalars['String']['input']>;
};

export type AssetLatestInfo = {
  __typename: 'AssetLatestInfo';
  assetKey: AssetKey;
  id: Scalars['ID']['output'];
  inProgressRunIds: Array<Scalars['String']['output']>;
  latestMaterialization: Maybe<MaterializationEvent>;
  latestRun: Maybe<Run>;
  unstartedRunIds: Array<Scalars['String']['output']>;
};

export type AssetLineageInfo = {
  __typename: 'AssetLineageInfo';
  assetKey: AssetKey;
  partitions: Array<Scalars['String']['output']>;
};

export {AssetMaterializationFailureReason};

export {AssetMaterializationFailureType};

export type AssetMaterializationPlannedEvent = MessageEvent &
  RunEvent & {
    __typename: 'AssetMaterializationPlannedEvent';
    assetKey: Maybe<AssetKey>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type AssetMetadataEntry = MetadataEntry & {
  __typename: 'AssetMetadataEntry';
  assetKey: AssetKey;
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
};

export type AssetNode = {
  __typename: 'AssetNode';
  assetCheckOrError: AssetCheckOrError;
  assetChecksOrError: AssetChecksOrError;
  assetKey: AssetKey;
  assetMaterializationUsedData: Array<MaterializationUpstreamDataVersion>;
  assetMaterializations: Array<MaterializationEvent>;
  assetObservations: Array<ObservationEvent>;
  assetPartitionStatuses: AssetPartitionStatuses;
  assetsForSameStorageAddress: Array<AssetNode>;
  autoMaterializePolicy: Maybe<AutoMaterializePolicy>;
  automationCondition: Maybe<AutomationCondition>;
  backfillPolicy: Maybe<BackfillPolicy>;
  changedReasons: Array<ChangeReason>;
  computeKind: Maybe<Scalars['String']['output']>;
  configField: Maybe<ConfigTypeField>;
  currentAutoMaterializeEvaluationId: Maybe<Scalars['ID']['output']>;
  dataVersion: Maybe<Scalars['String']['output']>;
  dataVersionByPartition: Array<Maybe<Scalars['String']['output']>>;
  dependedBy: Array<AssetDependency>;
  dependedByKeys: Array<AssetKey>;
  dependencies: Array<AssetDependency>;
  dependencyKeys: Array<AssetKey>;
  description: Maybe<Scalars['String']['output']>;
  freshnessInfo: Maybe<AssetFreshnessInfo>;
  freshnessPolicy: Maybe<FreshnessPolicy>;
  freshnessStatusInfo: Maybe<FreshnessStatusInfo>;
  graphName: Maybe<Scalars['String']['output']>;
  groupName: Scalars['String']['output'];
  hasAssetChecks: Scalars['Boolean']['output'];
  hasMaterializePermission: Scalars['Boolean']['output'];
  hasReportRunlessAssetEventPermission: Scalars['Boolean']['output'];
  hasWipePermission: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  internalFreshnessPolicy: Maybe<InternalFreshnessPolicy>;
  isAutoCreatedStub: Scalars['Boolean']['output'];
  isExecutable: Scalars['Boolean']['output'];
  isMaterializable: Scalars['Boolean']['output'];
  isObservable: Scalars['Boolean']['output'];
  isPartitioned: Scalars['Boolean']['output'];
  jobNames: Array<Scalars['String']['output']>;
  jobs: Array<Pipeline>;
  kinds: Array<Scalars['String']['output']>;
  lastAutoMaterializationEvaluationRecord: Maybe<AutoMaterializeAssetEvaluationRecord>;
  latestMaterializationByPartition: Array<Maybe<MaterializationEvent>>;
  latestRunForPartition: Maybe<Run>;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  op: Maybe<SolidDefinition>;
  opName: Maybe<Scalars['String']['output']>;
  opNames: Array<Scalars['String']['output']>;
  opVersion: Maybe<Scalars['String']['output']>;
  owners: Array<AssetOwner>;
  partitionDefinition: Maybe<PartitionDefinition>;
  partitionKeyConnection: Maybe<PartitionKeyConnection>;
  partitionKeys: Array<Scalars['String']['output']>;
  partitionKeysByDimension: Array<DimensionPartitionKeys>;
  partitionStats: Maybe<PartitionStats>;
  pools: Array<Scalars['String']['output']>;
  repository: Repository;
  requiredResources: Array<ResourceRequirement>;
  staleCauses: Array<StaleCause>;
  staleCausesByPartition: Maybe<Array<Array<StaleCause>>>;
  staleStatus: Maybe<StaleStatus>;
  staleStatusByPartition: Array<StaleStatus>;
  tags: Array<DefinitionTag>;
  targetingInstigators: Array<Instigator>;
  type: Maybe<ListDagsterType | NullableDagsterType | RegularDagsterType>;
};

export type AssetNodeAssetCheckOrErrorArgs = {
  checkName: Scalars['String']['input'];
};

export type AssetNodeAssetChecksOrErrorArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  pipeline?: InputMaybe<PipelineSelector>;
};

export type AssetNodeAssetMaterializationUsedDataArgs = {
  timestampMillis: Scalars['String']['input'];
};

export type AssetNodeAssetMaterializationsArgs = {
  beforeTimestampMillis?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  partitions?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type AssetNodeAssetObservationsArgs = {
  beforeTimestampMillis?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  partitions?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type AssetNodeDataVersionArgs = {
  partition?: InputMaybe<Scalars['String']['input']>;
};

export type AssetNodeDataVersionByPartitionArgs = {
  partitions?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type AssetNodeLastAutoMaterializationEvaluationRecordArgs = {
  asOfEvaluationId?: InputMaybe<Scalars['ID']['input']>;
};

export type AssetNodeLatestMaterializationByPartitionArgs = {
  partitions?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type AssetNodeLatestRunForPartitionArgs = {
  partition: Scalars['String']['input'];
};

export type AssetNodePartitionKeyConnectionArgs = {
  ascending: Scalars['Boolean']['input'];
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit: Scalars['Int']['input'];
};

export type AssetNodePartitionKeysByDimensionArgs = {
  endIdx?: InputMaybe<Scalars['Int']['input']>;
  startIdx?: InputMaybe<Scalars['Int']['input']>;
};

export type AssetNodeStaleCausesArgs = {
  partition?: InputMaybe<Scalars['String']['input']>;
};

export type AssetNodeStaleCausesByPartitionArgs = {
  partitions?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type AssetNodeStaleStatusArgs = {
  partition?: InputMaybe<Scalars['String']['input']>;
};

export type AssetNodeStaleStatusByPartitionArgs = {
  partitions?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type AssetNodeDefinitionCollision = {
  __typename: 'AssetNodeDefinitionCollision';
  assetKey: AssetKey;
  repositories: Array<Repository>;
};

export type AssetNodeOrError = AssetNode | AssetNotFoundError;

export type AssetNotFoundError = Error & {
  __typename: 'AssetNotFoundError';
  message: Scalars['String']['output'];
};

export type AssetOrError = Asset | AssetNotFoundError;

export type AssetOwner = TeamAssetOwner | UserAssetOwner;

export type AssetPartitionRange = {
  __typename: 'AssetPartitionRange';
  assetKey: AssetKey;
  partitionRange: Maybe<PartitionRange>;
};

export type AssetPartitionStatuses =
  | DefaultPartitionStatuses
  | MultiPartitionStatuses
  | TimePartitionStatuses;

export type AssetPartitions = {
  __typename: 'AssetPartitions';
  assetKey: AssetKey;
  partitions: Maybe<AssetBackfillTargetPartitions>;
};

export type AssetPartitionsStatusCounts = {
  __typename: 'AssetPartitionsStatusCounts';
  assetKey: AssetKey;
  numPartitionsFailed: Scalars['Int']['output'];
  numPartitionsInProgress: Scalars['Int']['output'];
  numPartitionsMaterialized: Scalars['Int']['output'];
  numPartitionsTargeted: Scalars['Int']['output'];
};

export type AssetRecord = {
  __typename: 'AssetRecord';
  id: Scalars['String']['output'];
  key: AssetKey;
};

export type AssetRecordConnection = {
  __typename: 'AssetRecordConnection';
  assets: Array<AssetRecord>;
  cursor: Maybe<Scalars['String']['output']>;
};

export type AssetRecordsOrError = AssetRecordConnection | PythonError;

export type AssetResultEventHistoryConnection = {
  __typename: 'AssetResultEventHistoryConnection';
  cursor: Scalars['String']['output'];
  results: Array<AssetResultEventType>;
};

export type AssetResultEventType =
  | FailedToMaterializeEvent
  | MaterializationEvent
  | ObservationEvent;

export type AssetSelection = {
  __typename: 'AssetSelection';
  assetChecks: Array<AssetCheckhandle>;
  assetKeys: Array<AssetKey>;
  assetSelectionString: Maybe<Scalars['String']['output']>;
  assets: Array<Asset>;
  assetsOrError: AssetsOrError;
};

export type AssetWipeMutationResult =
  | AssetNotFoundError
  | AssetWipeSuccess
  | PythonError
  | UnauthorizedError
  | UnsupportedOperationError;

export type AssetWipeSuccess = {
  __typename: 'AssetWipeSuccess';
  assetPartitionRanges: Array<AssetPartitionRange>;
};

export type AssetsOrError = AssetConnection | PythonError;

export type AutoMaterializeAssetEvaluationNeedsMigrationError = Error & {
  __typename: 'AutoMaterializeAssetEvaluationNeedsMigrationError';
  message: Scalars['String']['output'];
};

export type AutoMaterializeAssetEvaluationRecord = {
  __typename: 'AutoMaterializeAssetEvaluationRecord';
  assetKey: AssetKey;
  evaluationId: Scalars['ID']['output'];
  id: Scalars['ID']['output'];
  numDiscarded: Scalars['Int']['output'];
  numRequested: Scalars['Int']['output'];
  numSkipped: Scalars['Int']['output'];
  rules: Maybe<Array<AutoMaterializeRule>>;
  rulesWithRuleEvaluations: Array<AutoMaterializeRuleWithRuleEvaluations>;
  runIds: Array<Scalars['String']['output']>;
  timestamp: Scalars['Float']['output'];
};

export type AutoMaterializeAssetEvaluationRecords = {
  __typename: 'AutoMaterializeAssetEvaluationRecords';
  records: Array<AutoMaterializeAssetEvaluationRecord>;
};

export type AutoMaterializeAssetEvaluationRecordsOrError =
  | AutoMaterializeAssetEvaluationNeedsMigrationError
  | AutoMaterializeAssetEvaluationRecords;

export {AutoMaterializeDecisionType};

export type AutoMaterializePolicy = {
  __typename: 'AutoMaterializePolicy';
  maxMaterializationsPerMinute: Maybe<Scalars['Int']['output']>;
  policyType: AutoMaterializePolicyType;
  rules: Array<AutoMaterializeRule>;
};

export {AutoMaterializePolicyType};

export type AutoMaterializeRule = {
  __typename: 'AutoMaterializeRule';
  className: Scalars['String']['output'];
  decisionType: AutoMaterializeDecisionType;
  description: Scalars['String']['output'];
};

export type AutoMaterializeRuleEvaluation = {
  __typename: 'AutoMaterializeRuleEvaluation';
  evaluationData: Maybe<AutoMaterializeRuleEvaluationData>;
  partitionKeysOrError: Maybe<PartitionKeysOrError>;
};

export type AutoMaterializeRuleEvaluationData =
  | ParentMaterializedRuleEvaluationData
  | TextRuleEvaluationData
  | WaitingOnKeysRuleEvaluationData;

export type AutoMaterializeRuleWithRuleEvaluations = {
  __typename: 'AutoMaterializeRuleWithRuleEvaluations';
  rule: AutoMaterializeRule;
  ruleEvaluations: Array<AutoMaterializeRuleEvaluation>;
};

export type AutomationCondition = {
  __typename: 'AutomationCondition';
  expandedLabel: Array<Scalars['String']['output']>;
  label: Maybe<Scalars['String']['output']>;
};

export type AutomationConditionEvaluationNode = {
  __typename: 'AutomationConditionEvaluationNode';
  childUniqueIds: Array<Scalars['String']['output']>;
  endTimestamp: Maybe<Scalars['Float']['output']>;
  entityKey: EntityKey;
  expandedLabel: Array<Scalars['String']['output']>;
  isPartitioned: Scalars['Boolean']['output'];
  numCandidates: Maybe<Scalars['Int']['output']>;
  numTrue: Maybe<Scalars['Int']['output']>;
  operatorType: Scalars['String']['output'];
  sinceMetadata: Maybe<SinceConditionMetadata>;
  startTimestamp: Maybe<Scalars['Float']['output']>;
  uniqueId: Scalars['String']['output'];
  userLabel: Maybe<Scalars['String']['output']>;
};

export type BackfillNotFoundError = Error & {
  __typename: 'BackfillNotFoundError';
  backfillId: Scalars['String']['output'];
  message: Scalars['String']['output'];
};

export type BackfillPolicy = {
  __typename: 'BackfillPolicy';
  description: Scalars['String']['output'];
  maxPartitionsPerRun: Maybe<Scalars['Int']['output']>;
  policyType: BackfillPolicyType;
};

export {BackfillPolicyType};

export type BoolMetadataEntry = MetadataEntry & {
  __typename: 'BoolMetadataEntry';
  boolValue: Maybe<Scalars['Boolean']['output']>;
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
};

export {BulkActionStatus};

export type BulkActionsFilter = {
  createdAfter?: InputMaybe<Scalars['Float']['input']>;
  createdBefore?: InputMaybe<Scalars['Float']['input']>;
  statuses?: InputMaybe<Array<BulkActionStatus>>;
};

export type CancelBackfillResult = CancelBackfillSuccess | PythonError | UnauthorizedError;

export type CancelBackfillSuccess = {
  __typename: 'CancelBackfillSuccess';
  backfillId: Scalars['String']['output'];
};

export type CapturedLogs = {
  __typename: 'CapturedLogs';
  cursor: Maybe<Scalars['String']['output']>;
  logKey: Array<Scalars['String']['output']>;
  stderr: Maybe<Scalars['String']['output']>;
  stdout: Maybe<Scalars['String']['output']>;
};

export type CapturedLogsMetadata = {
  __typename: 'CapturedLogsMetadata';
  stderrDownloadUrl: Maybe<Scalars['String']['output']>;
  stderrLocation: Maybe<Scalars['String']['output']>;
  stdoutDownloadUrl: Maybe<Scalars['String']['output']>;
  stdoutLocation: Maybe<Scalars['String']['output']>;
};

export {ChangeReason};

export type ClaimedConcurrencySlot = {
  __typename: 'ClaimedConcurrencySlot';
  runId: Scalars['String']['output'];
  stepKey: Scalars['String']['output'];
};

export type CodeReferencesMetadataEntry = MetadataEntry & {
  __typename: 'CodeReferencesMetadataEntry';
  codeReferences: Array<SourceLocation>;
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
};

export type CompositeConfigType = ConfigType & {
  __typename: 'CompositeConfigType';
  description: Maybe<Scalars['String']['output']>;
  fields: Array<ConfigTypeField>;
  isSelector: Scalars['Boolean']['output'];
  key: Scalars['String']['output'];
  recursiveConfigTypes: Array<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
  typeParamKeys: Array<Scalars['String']['output']>;
};

export type CompositeSolidDefinition = ISolidDefinition &
  SolidContainer & {
    __typename: 'CompositeSolidDefinition';
    assetNodes: Array<AssetNode>;
    description: Maybe<Scalars['String']['output']>;
    id: Scalars['ID']['output'];
    inputDefinitions: Array<InputDefinition>;
    inputMappings: Array<InputMapping>;
    metadata: Array<MetadataItemDefinition>;
    modes: Array<Mode>;
    name: Scalars['String']['output'];
    outputDefinitions: Array<OutputDefinition>;
    outputMappings: Array<OutputMapping>;
    pools: Array<Scalars['String']['output']>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
  };

export type CompositeSolidDefinitionSolidHandleArgs = {
  handleID: Scalars['String']['input'];
};

export type CompositeSolidDefinitionSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']['input']>;
};

export type ConcurrencyKeyInfo = {
  __typename: 'ConcurrencyKeyInfo';
  activeRunIds: Array<Scalars['String']['output']>;
  activeSlotCount: Scalars['Int']['output'];
  assignedStepCount: Scalars['Int']['output'];
  assignedStepRunIds: Array<Scalars['String']['output']>;
  claimedSlots: Array<ClaimedConcurrencySlot>;
  concurrencyKey: Scalars['String']['output'];
  limit: Maybe<Scalars['Int']['output']>;
  pendingStepCount: Scalars['Int']['output'];
  pendingStepRunIds: Array<Scalars['String']['output']>;
  pendingSteps: Array<PendingConcurrencyStep>;
  slotCount: Scalars['Int']['output'];
  usingDefaultLimit: Maybe<Scalars['Boolean']['output']>;
};

export type ConfigType = {
  description: Maybe<Scalars['String']['output']>;
  isSelector: Scalars['Boolean']['output'];
  key: Scalars['String']['output'];
  recursiveConfigTypes: Array<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
  typeParamKeys: Array<Scalars['String']['output']>;
};

export type ConfigTypeField = {
  __typename: 'ConfigTypeField';
  configType:
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType;
  configTypeKey: Scalars['String']['output'];
  defaultValueAsJson: Maybe<Scalars['String']['output']>;
  description: Maybe<Scalars['String']['output']>;
  isRequired: Scalars['Boolean']['output'];
  isSecret: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
};

export type ConfigTypeNotFoundError = Error & {
  __typename: 'ConfigTypeNotFoundError';
  configTypeName: Scalars['String']['output'];
  message: Scalars['String']['output'];
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
  key: Scalars['String']['output'];
  type: ConfiguredValueType;
  value: Scalars['String']['output'];
};

export {ConfiguredValueType};

export type ConflictingExecutionParamsError = Error & {
  __typename: 'ConflictingExecutionParamsError';
  message: Scalars['String']['output'];
};

export type CronFreshnessPolicy = {
  __typename: 'CronFreshnessPolicy';
  deadlineCron: Scalars['String']['output'];
  lowerBoundDeltaSeconds: Scalars['Int']['output'];
  timezone: Scalars['String']['output'];
};

export type DaemonHealth = {
  __typename: 'DaemonHealth';
  allDaemonStatuses: Array<DaemonStatus>;
  daemonStatus: DaemonStatus;
  id: Scalars['String']['output'];
};

export type DaemonHealthDaemonStatusArgs = {
  daemonType?: InputMaybe<Scalars['String']['input']>;
};

export type DaemonStatus = {
  __typename: 'DaemonStatus';
  daemonType: Scalars['String']['output'];
  healthy: Maybe<Scalars['Boolean']['output']>;
  id: Scalars['ID']['output'];
  lastHeartbeatErrors: Array<PythonError>;
  lastHeartbeatTime: Maybe<Scalars['Float']['output']>;
  required: Scalars['Boolean']['output'];
};

export {DagsterEventType};

export type DagsterLibraryVersion = {
  __typename: 'DagsterLibraryVersion';
  name: Scalars['String']['output'];
  version: Scalars['String']['output'];
};

export type DagsterRunEvent =
  | AlertFailureEvent
  | AlertStartEvent
  | AlertSuccessEvent
  | AssetCheckEvaluationEvent
  | AssetCheckEvaluationPlannedEvent
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
  | FailedToMaterializeEvent
  | HandledOutputEvent
  | HealthChangedEvent
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
  description: Maybe<Scalars['String']['output']>;
  displayName: Scalars['String']['output'];
  innerTypes: Array<ListDagsterType | NullableDagsterType | RegularDagsterType>;
  inputSchemaType: Maybe<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
  isBuiltin: Scalars['Boolean']['output'];
  isList: Scalars['Boolean']['output'];
  isNothing: Scalars['Boolean']['output'];
  isNullable: Scalars['Boolean']['output'];
  key: Scalars['String']['output'];
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  name: Maybe<Scalars['String']['output']>;
  outputSchemaType: Maybe<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
};

export type DagsterTypeNotFoundError = Error & {
  __typename: 'DagsterTypeNotFoundError';
  dagsterTypeName: Scalars['String']['output'];
  message: Scalars['String']['output'];
};

export type DagsterTypeOrError =
  | DagsterTypeNotFoundError
  | PipelineNotFoundError
  | PythonError
  | RegularDagsterType;

export type DefaultPartitionStatuses = {
  __typename: 'DefaultPartitionStatuses';
  failedPartitions: Array<Scalars['String']['output']>;
  materializedPartitions: Array<Scalars['String']['output']>;
  materializingPartitions: Array<Scalars['String']['output']>;
  unmaterializedPartitions: Array<Scalars['String']['output']>;
};

export type DefinitionOwner = TeamDefinitionOwner | UserDefinitionOwner;

export type DefinitionTag = {
  __typename: 'DefinitionTag';
  key: Scalars['String']['output'];
  value: Scalars['String']['output'];
};

export {DefinitionsSource};

export type DefsKeyStateInfo = {
  __typename: 'DefsKeyStateInfo';
  createTimestamp: Scalars['Float']['output'];
  managementType: DefsStateManagementType;
  version: Scalars['String']['output'];
};

export type DefsStateInfo = {
  __typename: 'DefsStateInfo';
  keyStateInfo: Array<DefsStateInfoEntry>;
};

export type DefsStateInfoEntry = {
  __typename: 'DefsStateInfoEntry';
  info: Maybe<DefsKeyStateInfo>;
  name: Scalars['String']['output'];
};

export {DefsStateManagementType};

export type DeleteDynamicPartitionsResult =
  | DeleteDynamicPartitionsSuccess
  | PythonError
  | UnauthorizedError;

export type DeleteDynamicPartitionsSuccess = {
  __typename: 'DeleteDynamicPartitionsSuccess';
  partitionsDefName: Scalars['String']['output'];
};

export type DeletePipelineRunResult =
  | DeletePipelineRunSuccess
  | PythonError
  | RunNotFoundError
  | UnauthorizedError;

export type DeletePipelineRunSuccess = {
  __typename: 'DeletePipelineRunSuccess';
  runId: Scalars['String']['output'];
};

export type DeleteRunMutation = {
  __typename: 'DeleteRunMutation';
  Output: DeletePipelineRunResult;
};

export type DimensionDefinitionType = {
  __typename: 'DimensionDefinitionType';
  description: Scalars['String']['output'];
  dynamicPartitionsDefinitionName: Maybe<Scalars['String']['output']>;
  isPrimaryDimension: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  type: PartitionDefinitionType;
};

export type DimensionPartitionKeys = {
  __typename: 'DimensionPartitionKeys';
  name: Scalars['String']['output'];
  partitionKeys: Array<Scalars['String']['output']>;
  type: PartitionDefinitionType;
};

export type DisplayableEvent = {
  description: Maybe<Scalars['String']['output']>;
  label: Maybe<Scalars['String']['output']>;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
};

export type DryRunInstigationTick = {
  __typename: 'DryRunInstigationTick';
  evaluationResult: Maybe<TickEvaluation>;
  timestamp: Maybe<Scalars['Float']['output']>;
};

export type DryRunInstigationTicks = {
  __typename: 'DryRunInstigationTicks';
  cursor: Scalars['Float']['output'];
  results: Array<DryRunInstigationTick>;
};

export type DuplicateDynamicPartitionError = Error & {
  __typename: 'DuplicateDynamicPartitionError';
  message: Scalars['String']['output'];
  partitionName: Scalars['String']['output'];
  partitionsDefName: Scalars['String']['output'];
};

export type DynamicPartitionRequest = {
  __typename: 'DynamicPartitionRequest';
  partitionKeys: Maybe<Array<Scalars['String']['output']>>;
  partitionsDefName: Scalars['String']['output'];
  type: DynamicPartitionsRequestType;
};

export type DynamicPartitionsRequestResult = {
  __typename: 'DynamicPartitionsRequestResult';
  partitionKeys: Maybe<Array<Scalars['String']['output']>>;
  partitionsDefName: Scalars['String']['output'];
  skippedPartitionKeys: Array<Scalars['String']['output']>;
  type: DynamicPartitionsRequestType;
};

export {DynamicPartitionsRequestType};

export type EngineEvent = DisplayableEvent &
  ErrorEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'EngineEvent';
    description: Maybe<Scalars['String']['output']>;
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']['output']>;
    markerStart: Maybe<Scalars['String']['output']>;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type EntityKey = AssetCheckhandle | AssetKey;

export type EnumConfigType = ConfigType & {
  __typename: 'EnumConfigType';
  description: Maybe<Scalars['String']['output']>;
  givenName: Scalars['String']['output'];
  isSelector: Scalars['Boolean']['output'];
  key: Scalars['String']['output'];
  recursiveConfigTypes: Array<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
  typeParamKeys: Array<Scalars['String']['output']>;
  values: Array<EnumConfigValue>;
};

export type EnumConfigValue = {
  __typename: 'EnumConfigValue';
  description: Maybe<Scalars['String']['output']>;
  value: Scalars['String']['output'];
};

export type EnvVarConsumer = {
  __typename: 'EnvVarConsumer';
  name: Scalars['String']['output'];
  type: EnvVarConsumerType;
};

export {EnvVarConsumerType};

export type EnvVarWithConsumers = {
  __typename: 'EnvVarWithConsumers';
  envVarConsumers: Array<EnvVarConsumer>;
  envVarName: Scalars['String']['output'];
};

export type EnvVarWithConsumersList = {
  __typename: 'EnvVarWithConsumersList';
  results: Array<EnvVarWithConsumers>;
};

export type EnvVarWithConsumersOrError = EnvVarWithConsumersList | PythonError;

export type Error = {
  message: Scalars['String']['output'];
};

export type ErrorChainLink = Error & {
  __typename: 'ErrorChainLink';
  error: PythonError;
  isExplicitLink: Scalars['Boolean']['output'];
  message: Scalars['String']['output'];
};

export type ErrorEvent = {
  error: Maybe<PythonError>;
};

export {ErrorSource};

export {EvaluationErrorReason};

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
  listIndex: Scalars['Int']['output'];
};

export type EvaluationStackMapKeyEntry = {
  __typename: 'EvaluationStackMapKeyEntry';
  mapKey: Scalars['GenericScalar']['output'];
};

export type EvaluationStackMapValueEntry = {
  __typename: 'EvaluationStackMapValueEntry';
  mapKey: Scalars['GenericScalar']['output'];
};

export type EvaluationStackPathEntry = {
  __typename: 'EvaluationStackPathEntry';
  fieldName: Scalars['String']['output'];
};

export type EventConnection = {
  __typename: 'EventConnection';
  cursor: Scalars['String']['output'];
  events: Array<DagsterRunEvent>;
  hasMore: Scalars['Boolean']['output'];
};

export type EventConnectionOrError = EventConnection | PythonError | RunNotFoundError;

export type EventTag = {
  __typename: 'EventTag';
  key: Scalars['String']['output'];
  value: Scalars['String']['output'];
};

export type ExecutionMetadata = {
  parentRunId?: InputMaybe<Scalars['String']['input']>;
  rootRunId?: InputMaybe<Scalars['String']['input']>;
  tags?: InputMaybe<Array<ExecutionTag>>;
};

export type ExecutionParams = {
  executionMetadata?: InputMaybe<ExecutionMetadata>;
  mode?: InputMaybe<Scalars['String']['input']>;
  preset?: InputMaybe<Scalars['String']['input']>;
  runConfigData?: InputMaybe<Scalars['RunConfigData']['input']>;
  selector: JobOrPipelineSelector;
  stepKeys?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type ExecutionPlan = {
  __typename: 'ExecutionPlan';
  artifactsPersisted: Scalars['Boolean']['output'];
  assetKeys: Array<AssetKey>;
  assetSelection: Array<Scalars['String']['output']>;
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
  key: Scalars['String']['output'];
  kind: StepKind;
  metadata: Array<MetadataItemDefinition>;
  outputs: Array<ExecutionStepOutput>;
  solidHandleID: Scalars['String']['output'];
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
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ExecutionStepInput = {
  __typename: 'ExecutionStepInput';
  dependsOn: Array<ExecutionStep>;
  name: Scalars['String']['output'];
};

export type ExecutionStepInputEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepInputEvent';
    eventType: Maybe<DagsterEventType>;
    inputName: Scalars['String']['output'];
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
    typeCheck: TypeCheck;
  };

export type ExecutionStepOutput = {
  __typename: 'ExecutionStepOutput';
  name: Scalars['String']['output'];
};

export type ExecutionStepOutputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepOutputEvent';
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    outputName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
    typeCheck: TypeCheck;
  };

export type ExecutionStepRestartEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepRestartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ExecutionStepSkippedEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepSkippedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ExecutionStepStartEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepStartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ExecutionStepSuccessEvent = MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepSuccessEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ExecutionStepUpForRetryEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ExecutionStepUpForRetryEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    secondsToWait: Maybe<Scalars['Float']['output']>;
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ExecutionTag = {
  key: Scalars['String']['input'];
  value: Scalars['String']['input'];
};

export type ExpectationResult = DisplayableEvent & {
  __typename: 'ExpectationResult';
  description: Maybe<Scalars['String']['output']>;
  label: Maybe<Scalars['String']['output']>;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  success: Scalars['Boolean']['output'];
};

export type FailedToMaterializeEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'FailedToMaterializeEvent';
    assetKey: Maybe<AssetKey>;
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    materializationFailureReason: AssetMaterializationFailureReason;
    materializationFailureType: AssetMaterializationFailureType;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    partition: Maybe<Scalars['String']['output']>;
    runId: Scalars['String']['output'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    stepStats: RunStepStats;
    tags: Array<EventTag>;
    timestamp: Scalars['String']['output'];
  };

export type FailureMetadata = DisplayableEvent & {
  __typename: 'FailureMetadata';
  description: Maybe<Scalars['String']['output']>;
  label: Maybe<Scalars['String']['output']>;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
};

export type FeatureFlag = {
  __typename: 'FeatureFlag';
  enabled: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
};

export type FieldNotDefinedConfigError = PipelineConfigValidationError & {
  __typename: 'FieldNotDefinedConfigError';
  fieldName: Scalars['String']['output'];
  message: Scalars['String']['output'];
  path: Array<Scalars['String']['output']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type FieldsNotDefinedConfigError = PipelineConfigValidationError & {
  __typename: 'FieldsNotDefinedConfigError';
  fieldNames: Array<Scalars['String']['output']>;
  message: Scalars['String']['output'];
  path: Array<Scalars['String']['output']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type FloatMetadataEntry = MetadataEntry & {
  __typename: 'FloatMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  floatRepr: Scalars['String']['output'];
  floatValue: Maybe<Scalars['Float']['output']>;
  label: Scalars['String']['output'];
};

export type FreshnessPolicy = {
  __typename: 'FreshnessPolicy';
  cronSchedule: Maybe<Scalars['String']['output']>;
  cronScheduleTimezone: Maybe<Scalars['String']['output']>;
  lastEvaluationTimestamp: Maybe<Scalars['String']['output']>;
  maximumLagMinutes: Scalars['Float']['output'];
};

export type FreshnessStatusInfo = {
  __typename: 'FreshnessStatusInfo';
  freshnessStatus: AssetHealthStatus;
  freshnessStatusMetadata: Maybe<AssetHealthFreshnessMeta>;
};

export type Graph = SolidContainer & {
  __typename: 'Graph';
  description: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  modes: Array<Mode>;
  name: Scalars['String']['output'];
  solidHandle: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
};

export type GraphSolidHandleArgs = {
  handleID: Scalars['String']['input'];
};

export type GraphSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']['input']>;
};

export type GraphNotFoundError = Error & {
  __typename: 'GraphNotFoundError';
  graphName: Scalars['String']['output'];
  message: Scalars['String']['output'];
  repositoryLocationName: Scalars['String']['output'];
  repositoryName: Scalars['String']['output'];
};

export type GraphOrError = Graph | GraphNotFoundError | PythonError;

export type GraphSelector = {
  graphName: Scalars['String']['input'];
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
};

export type HandledOutputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'HandledOutputEvent';
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    managerKey: Scalars['String']['output'];
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    outputName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type HealthChangedEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'HealthChangedEvent';
    assetKey: Maybe<AssetKey>;
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    partition: Maybe<Scalars['String']['output']>;
    runId: Scalars['String']['output'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    stepStats: RunStepStats;
    tags: Array<EventTag>;
    timestamp: Scalars['String']['output'];
  };

export type HookCompletedEvent = MessageEvent &
  StepEvent & {
    __typename: 'HookCompletedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type HookErroredEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'HookErroredEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type HookSkippedEvent = MessageEvent &
  StepEvent & {
    __typename: 'HookSkippedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type IPipelineSnapshot = {
  dagsterTypeOrError: DagsterTypeOrError;
  dagsterTypes: Array<ListDagsterType | NullableDagsterType | RegularDagsterType>;
  description: Maybe<Scalars['String']['output']>;
  graphName: Scalars['String']['output'];
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  modes: Array<Mode>;
  name: Scalars['String']['output'];
  owners: Array<DefinitionOwner>;
  parentSnapshotId: Maybe<Scalars['String']['output']>;
  pipelineSnapshotId: Scalars['String']['output'];
  runs: Array<Run>;
  schedules: Array<Schedule>;
  sensors: Array<Sensor>;
  solidHandle: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
  tags: Array<PipelineTag>;
};

export type IPipelineSnapshotDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String']['input'];
};

export type IPipelineSnapshotRunsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type IPipelineSnapshotSolidHandleArgs = {
  handleID: Scalars['String']['input'];
};

export type IPipelineSnapshotSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']['input']>;
};

export type ISolidDefinition = {
  assetNodes: Array<AssetNode>;
  description: Maybe<Scalars['String']['output']>;
  inputDefinitions: Array<InputDefinition>;
  metadata: Array<MetadataItemDefinition>;
  name: Scalars['String']['output'];
  outputDefinitions: Array<OutputDefinition>;
  pools: Array<Scalars['String']['output']>;
};

export type Input = {
  __typename: 'Input';
  definition: InputDefinition;
  dependsOn: Array<Output>;
  isDynamicCollect: Scalars['Boolean']['output'];
  solid: Solid;
};

export type InputDefinition = {
  __typename: 'InputDefinition';
  description: Maybe<Scalars['String']['output']>;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  name: Scalars['String']['output'];
  type: ListDagsterType | NullableDagsterType | RegularDagsterType;
};

export type InputMapping = {
  __typename: 'InputMapping';
  definition: InputDefinition;
  mappedInput: Input;
};

export type Instance = {
  __typename: 'Instance';
  autoMaterializePaused: Scalars['Boolean']['output'];
  concurrencyLimit: ConcurrencyKeyInfo;
  concurrencyLimits: Array<ConcurrencyKeyInfo>;
  daemonHealth: DaemonHealth;
  executablePath: Scalars['String']['output'];
  freshnessEvaluationEnabled: Scalars['Boolean']['output'];
  hasInfo: Scalars['Boolean']['output'];
  id: Scalars['String']['output'];
  info: Maybe<Scalars['String']['output']>;
  maxConcurrencyLimitValue: Scalars['Int']['output'];
  minConcurrencyLimitValue: Scalars['Int']['output'];
  poolConfig: Maybe<PoolConfig>;
  runLauncher: Maybe<RunLauncher>;
  runQueueConfig: Maybe<RunQueueConfig>;
  runQueuingSupported: Scalars['Boolean']['output'];
  supportsConcurrencyLimits: Scalars['Boolean']['output'];
  useAutoMaterializeSensors: Scalars['Boolean']['output'];
};

export type InstanceConcurrencyLimitArgs = {
  concurrencyKey?: InputMaybe<Scalars['String']['input']>;
};

export type InstigationEvent = {
  __typename: 'InstigationEvent';
  level: LogLevel;
  message: Scalars['String']['output'];
  timestamp: Scalars['String']['output'];
};

export type InstigationEventConnection = {
  __typename: 'InstigationEventConnection';
  cursor: Scalars['String']['output'];
  events: Array<InstigationEvent>;
  hasMore: Scalars['Boolean']['output'];
};

export type InstigationSelector = {
  name: Scalars['String']['input'];
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
};

export type InstigationState = {
  __typename: 'InstigationState';
  hasStartPermission: Scalars['Boolean']['output'];
  hasStopPermission: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  instigationType: InstigationType;
  name: Scalars['String']['output'];
  nextTick: Maybe<DryRunInstigationTick>;
  repositoryLocationName: Scalars['String']['output'];
  repositoryName: Scalars['String']['output'];
  repositoryOrigin: RepositoryOrigin;
  runningCount: Scalars['Int']['output'];
  runs: Array<Run>;
  runsCount: Scalars['Int']['output'];
  selectorId: Scalars['String']['output'];
  status: InstigationStatus;
  tick: InstigationTick;
  ticks: Array<InstigationTick>;
  typeSpecificData: Maybe<InstigationTypeSpecificData>;
};

export type InstigationStateRunsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type InstigationStateTickArgs = {
  tickId: Scalars['ID']['input'];
};

export type InstigationStateTicksArgs = {
  afterTimestamp?: InputMaybe<Scalars['Float']['input']>;
  beforeTimestamp?: InputMaybe<Scalars['Float']['input']>;
  cursor?: InputMaybe<Scalars['String']['input']>;
  dayOffset?: InputMaybe<Scalars['Int']['input']>;
  dayRange?: InputMaybe<Scalars['Int']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  statuses?: InputMaybe<Array<InstigationTickStatus>>;
};

export type InstigationStateNotFoundError = Error & {
  __typename: 'InstigationStateNotFoundError';
  message: Scalars['String']['output'];
  name: Scalars['String']['output'];
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

export {InstigationStatus};

export type InstigationTick = {
  __typename: 'InstigationTick';
  autoMaterializeAssetEvaluationId: Maybe<Scalars['ID']['output']>;
  cursor: Maybe<Scalars['String']['output']>;
  dynamicPartitionsRequestResults: Array<DynamicPartitionsRequestResult>;
  endTimestamp: Maybe<Scalars['Float']['output']>;
  error: Maybe<PythonError>;
  id: Scalars['ID']['output'];
  instigationType: InstigationType;
  logEvents: InstigationEventConnection;
  logKey: Maybe<Array<Scalars['String']['output']>>;
  originRunIds: Array<Scalars['String']['output']>;
  requestedAssetKeys: Array<AssetKey>;
  requestedAssetMaterializationCount: Scalars['Int']['output'];
  requestedMaterializationsForAssets: Array<RequestedMaterializationsForAsset>;
  runIds: Array<Scalars['String']['output']>;
  runKeys: Array<Scalars['String']['output']>;
  runs: Array<Run>;
  skipReason: Maybe<Scalars['String']['output']>;
  status: InstigationTickStatus;
  tickId: Scalars['ID']['output'];
  timestamp: Scalars['Float']['output'];
};

export {InstigationTickStatus};

export {InstigationType};

export type InstigationTypeSpecificData = ScheduleData | SensorData;

export type Instigator = Schedule | Sensor;

export type IntMetadataEntry = MetadataEntry & {
  __typename: 'IntMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  intRepr: Scalars['String']['output'];
  intValue: Maybe<Scalars['Int']['output']>;
  label: Scalars['String']['output'];
};

export type InternalFreshnessPolicy = CronFreshnessPolicy | TimeWindowFreshnessPolicy;

export type InvalidOutputError = {
  __typename: 'InvalidOutputError';
  invalidOutputName: Scalars['String']['output'];
  stepKey: Scalars['String']['output'];
};

export type InvalidPipelineRunsFilterError = Error & {
  __typename: 'InvalidPipelineRunsFilterError';
  message: Scalars['String']['output'];
};

export type InvalidStepError = {
  __typename: 'InvalidStepError';
  invalidStepKey: Scalars['String']['output'];
};

export type InvalidSubsetError = Error & {
  __typename: 'InvalidSubsetError';
  message: Scalars['String']['output'];
  pipeline: Pipeline;
};

export type Job = IPipelineSnapshot &
  SolidContainer & {
    __typename: 'Job';
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<ListDagsterType | NullableDagsterType | RegularDagsterType>;
    description: Maybe<Scalars['String']['output']>;
    externalJobSource: Maybe<Scalars['String']['output']>;
    graphName: Scalars['String']['output'];
    hasLaunchExecutionPermission: Scalars['Boolean']['output'];
    hasLaunchReexecutionPermission: Scalars['Boolean']['output'];
    id: Scalars['ID']['output'];
    isAssetJob: Scalars['Boolean']['output'];
    isJob: Scalars['Boolean']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    modes: Array<Mode>;
    name: Scalars['String']['output'];
    nodeNames: Array<Scalars['String']['output']>;
    owners: Array<DefinitionOwner>;
    parentSnapshotId: Maybe<Scalars['String']['output']>;
    partition: Maybe<PartitionTagsAndConfig>;
    partitionKeysOrError: PartitionKeys;
    pipelineSnapshotId: Scalars['String']['output'];
    presets: Array<PipelinePreset>;
    repository: Repository;
    runTags: Array<PipelineTag>;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type JobDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String']['input'];
};

export type JobPartitionArgs = {
  partitionName: Scalars['String']['input'];
  selectedAssetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type JobPartitionKeysOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  reverse?: InputMaybe<Scalars['Boolean']['input']>;
  selectedAssetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type JobRunsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type JobSolidHandleArgs = {
  handleID: Scalars['String']['input'];
};

export type JobSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']['input']>;
};

export type JobMetadataEntry = MetadataEntry & {
  __typename: 'JobMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  jobName: Scalars['String']['output'];
  label: Scalars['String']['output'];
  locationName: Scalars['String']['output'];
  repositoryName: Maybe<Scalars['String']['output']>;
};

export type JobOrPipelineSelector = {
  assetCheckSelection?: InputMaybe<Array<AssetCheckHandleInput>>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  jobName?: InputMaybe<Scalars['String']['input']>;
  pipelineName?: InputMaybe<Scalars['String']['input']>;
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  solidSelection?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type JobWithOps = {
  __typename: 'JobWithOps';
  jobName: Scalars['String']['output'];
  opHandleIDs: Array<Scalars['String']['output']>;
};

export type JsonMetadataEntry = MetadataEntry & {
  __typename: 'JsonMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  jsonString: Scalars['String']['output'];
  label: Scalars['String']['output'];
};

export type LaunchBackfillMutation = {
  __typename: 'LaunchBackfillMutation';
  Output: LaunchBackfillResult;
};

export type LaunchBackfillParams = {
  allPartitions?: InputMaybe<Scalars['Boolean']['input']>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  description?: InputMaybe<Scalars['String']['input']>;
  forceSynchronousSubmission?: InputMaybe<Scalars['Boolean']['input']>;
  fromFailure?: InputMaybe<Scalars['Boolean']['input']>;
  partitionNames?: InputMaybe<Array<Scalars['String']['input']>>;
  partitionsByAssets?: InputMaybe<Array<InputMaybe<PartitionsByAssetSelector>>>;
  reexecutionSteps?: InputMaybe<Array<Scalars['String']['input']>>;
  runConfigData?: InputMaybe<Scalars['RunConfigData']['input']>;
  selector?: InputMaybe<PartitionSetSelector>;
  tags?: InputMaybe<Array<ExecutionTag>>;
  title?: InputMaybe<Scalars['String']['input']>;
};

export type LaunchBackfillResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchBackfillSuccess
  | NoModeProvidedError
  | PartitionKeysNotFoundError
  | PartitionSetNotFoundError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchBackfillSuccess = {
  __typename: 'LaunchBackfillSuccess';
  backfillId: Scalars['String']['output'];
  launchedRunIds: Maybe<Array<Maybe<Scalars['String']['output']>>>;
};

export type LaunchMultipleRunsMutation = {
  __typename: 'LaunchMultipleRunsMutation';
  Output: LaunchMultipleRunsResultOrError;
};

export type LaunchMultipleRunsResult = {
  __typename: 'LaunchMultipleRunsResult';
  launchMultipleRunsResult: Array<LaunchRunResult>;
};

export type LaunchMultipleRunsResultOrError = LaunchMultipleRunsResult | PythonError;

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
    description: Maybe<Scalars['String']['output']>;
    displayName: Scalars['String']['output'];
    innerTypes: Array<ListDagsterType | NullableDagsterType | RegularDagsterType>;
    inputSchemaType: Maybe<
      | ArrayConfigType
      | CompositeConfigType
      | EnumConfigType
      | MapConfigType
      | NullableConfigType
      | RegularConfigType
      | ScalarUnionConfigType
    >;
    isBuiltin: Scalars['Boolean']['output'];
    isList: Scalars['Boolean']['output'];
    isNothing: Scalars['Boolean']['output'];
    isNullable: Scalars['Boolean']['output'];
    key: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    name: Maybe<Scalars['String']['output']>;
    ofType: ListDagsterType | NullableDagsterType | RegularDagsterType;
    outputSchemaType: Maybe<
      | ArrayConfigType
      | CompositeConfigType
      | EnumConfigType
      | MapConfigType
      | NullableConfigType
      | RegularConfigType
      | ScalarUnionConfigType
    >;
  };

export type LoadedInputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'LoadedInputEvent';
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    inputName: Scalars['String']['output'];
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    managerKey: Scalars['String']['output'];
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
    upstreamOutputName: Maybe<Scalars['String']['output']>;
    upstreamStepKey: Maybe<Scalars['String']['output']>;
  };

export type LocalFileCodeReference = {
  __typename: 'LocalFileCodeReference';
  filePath: Scalars['String']['output'];
  label: Maybe<Scalars['String']['output']>;
  lineNumber: Maybe<Scalars['Int']['output']>;
};

export type LocationDocsJson = {
  __typename: 'LocationDocsJson';
  json: Scalars['JSONString']['output'];
};

export type LocationDocsJsonOrError = LocationDocsJson | PythonError;

export type LocationStateChangeEvent = {
  __typename: 'LocationStateChangeEvent';
  eventType: LocationStateChangeEventType;
  locationName: Scalars['String']['output'];
  message: Scalars['String']['output'];
  serverId: Maybe<Scalars['String']['output']>;
};

export {LocationStateChangeEventType};

export type LocationStateChangeSubscription = {
  __typename: 'LocationStateChangeSubscription';
  event: LocationStateChangeEvent;
};

export {LogLevel};

export type LogMessageEvent = MessageEvent & {
  __typename: 'LogMessageEvent';
  eventType: Maybe<DagsterEventType>;
  level: LogLevel;
  message: Scalars['String']['output'];
  runId: Scalars['String']['output'];
  solidHandleID: Maybe<Scalars['String']['output']>;
  stepKey: Maybe<Scalars['String']['output']>;
  timestamp: Scalars['String']['output'];
};

export type LogRetrievalShellCommand = {
  __typename: 'LogRetrievalShellCommand';
  stderr: Maybe<Scalars['String']['output']>;
  stdout: Maybe<Scalars['String']['output']>;
};

export type LogTelemetryMutationResult = LogTelemetrySuccess | PythonError;

export type LogTelemetrySuccess = {
  __typename: 'LogTelemetrySuccess';
  action: Scalars['String']['output'];
};

export type Logger = {
  __typename: 'Logger';
  configField: Maybe<ConfigTypeField>;
  description: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
};

export type LogsCapturedEvent = MessageEvent & {
  __typename: 'LogsCapturedEvent';
  eventType: Maybe<DagsterEventType>;
  externalStderrUrl: Maybe<Scalars['String']['output']>;
  externalStdoutUrl: Maybe<Scalars['String']['output']>;
  externalUrl: Maybe<Scalars['String']['output']>;
  fileKey: Scalars['String']['output'];
  level: LogLevel;
  logKey: Scalars['String']['output'];
  message: Scalars['String']['output'];
  pid: Maybe<Scalars['Int']['output']>;
  runId: Scalars['String']['output'];
  shellCmd: Maybe<LogRetrievalShellCommand>;
  solidHandleID: Maybe<Scalars['String']['output']>;
  stepKey: Maybe<Scalars['String']['output']>;
  stepKeys: Maybe<Array<Scalars['String']['output']>>;
  timestamp: Scalars['String']['output'];
};

export type MapConfigType = ConfigType & {
  __typename: 'MapConfigType';
  description: Maybe<Scalars['String']['output']>;
  isSelector: Scalars['Boolean']['output'];
  key: Scalars['String']['output'];
  keyLabelName: Maybe<Scalars['String']['output']>;
  keyType:
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType;
  recursiveConfigTypes: Array<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
  typeParamKeys: Array<Scalars['String']['output']>;
  valueType:
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType;
};

export type MarkdownMetadataEntry = MetadataEntry & {
  __typename: 'MarkdownMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  mdStr: Scalars['String']['output'];
};

export type MarkerEvent = {
  markerEnd: Maybe<Scalars['String']['output']>;
  markerStart: Maybe<Scalars['String']['output']>;
};

export type MarshalledInput = {
  inputName: Scalars['String']['input'];
  key: Scalars['String']['input'];
};

export type MarshalledOutput = {
  key: Scalars['String']['input'];
  outputName: Scalars['String']['input'];
};

export type MaterializationEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'MaterializationEvent';
    assetKey: Maybe<AssetKey>;
    assetLineage: Array<AssetLineageInfo>;
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    partition: Maybe<Scalars['String']['output']>;
    runId: Scalars['String']['output'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    stepStats: RunStepStats;
    tags: Array<EventTag>;
    timestamp: Scalars['String']['output'];
  };

export type MaterializationUpstreamDataVersion = {
  __typename: 'MaterializationUpstreamDataVersion';
  assetKey: AssetKey;
  downstreamAssetKey: AssetKey;
  timestamp: Scalars['String']['output'];
};

export type MaterializedPartitionRangeStatuses2D = {
  __typename: 'MaterializedPartitionRangeStatuses2D';
  primaryDimEndKey: Scalars['String']['output'];
  primaryDimEndTime: Maybe<Scalars['Float']['output']>;
  primaryDimStartKey: Scalars['String']['output'];
  primaryDimStartTime: Maybe<Scalars['Float']['output']>;
  secondaryDim: PartitionStatus1D;
};

export type MessageEvent = {
  eventType: Maybe<DagsterEventType>;
  level: LogLevel;
  message: Scalars['String']['output'];
  runId: Scalars['String']['output'];
  solidHandleID: Maybe<Scalars['String']['output']>;
  stepKey: Maybe<Scalars['String']['output']>;
  timestamp: Scalars['String']['output'];
};

export type MetadataEntry = {
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
};

export type MetadataItemDefinition = {
  __typename: 'MetadataItemDefinition';
  key: Scalars['String']['output'];
  value: Scalars['String']['output'];
};

export type MissingFieldConfigError = PipelineConfigValidationError & {
  __typename: 'MissingFieldConfigError';
  field: ConfigTypeField;
  message: Scalars['String']['output'];
  path: Array<Scalars['String']['output']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type MissingFieldsConfigError = PipelineConfigValidationError & {
  __typename: 'MissingFieldsConfigError';
  fields: Array<ConfigTypeField>;
  message: Scalars['String']['output'];
  path: Array<Scalars['String']['output']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type MissingRunIdErrorEvent = {
  __typename: 'MissingRunIdErrorEvent';
  invalidRunId: Scalars['String']['output'];
};

export type Mode = {
  __typename: 'Mode';
  description: Maybe<Scalars['String']['output']>;
  id: Scalars['String']['output'];
  loggers: Array<Logger>;
  name: Scalars['String']['output'];
  resources: Array<Resource>;
};

export type ModeNotFoundError = Error & {
  __typename: 'ModeNotFoundError';
  message: Scalars['String']['output'];
  mode: Scalars['String']['output'];
};

export type MultiPartitionStatuses = {
  __typename: 'MultiPartitionStatuses';
  primaryDimensionName: Scalars['String']['output'];
  ranges: Array<MaterializedPartitionRangeStatuses2D>;
};

export type Mutation = {
  __typename: 'Mutation';
  addDynamicPartition: AddDynamicPartitionResult;
  cancelPartitionBackfill: CancelBackfillResult;
  deleteConcurrencyLimit: Scalars['Boolean']['output'];
  deleteDynamicPartitions: DeleteDynamicPartitionsResult;
  deletePipelineRun: DeletePipelineRunResult;
  deleteRun: DeletePipelineRunResult;
  freeConcurrencySlots: Scalars['Boolean']['output'];
  freeConcurrencySlotsForRun: Scalars['Boolean']['output'];
  launchMultipleRuns: LaunchMultipleRunsResultOrError;
  launchPartitionBackfill: LaunchBackfillResult;
  launchPipelineExecution: LaunchRunResult;
  launchPipelineReexecution: LaunchRunReexecutionResult;
  launchRun: LaunchRunResult;
  launchRunReexecution: LaunchRunReexecutionResult;
  logTelemetry: LogTelemetryMutationResult;
  reexecutePartitionBackfill: LaunchBackfillResult;
  reloadRepositoryLocation: ReloadRepositoryLocationMutationResult;
  reloadWorkspace: ReloadWorkspaceMutationResult;
  reportAssetCheckEvaluation: ReportAssetCheckEvaluationResult;
  reportRunlessAssetEvents: ReportRunlessAssetEventsResult;
  resetSchedule: ScheduleMutationResult;
  resetSensor: SensorOrError;
  resumePartitionBackfill: ResumeBackfillResult;
  scheduleDryRun: ScheduleDryRunResult;
  sensorDryRun: SensorDryRunResult;
  setAutoMaterializePaused: Scalars['Boolean']['output'];
  setConcurrencyLimit: Scalars['Boolean']['output'];
  setNuxSeen: Scalars['Boolean']['output'];
  setSensorCursor: SensorOrError;
  shutdownRepositoryLocation: ShutdownRepositoryLocationMutationResult;
  startSchedule: ScheduleMutationResult;
  startSensor: SensorOrError;
  stopRunningSchedule: ScheduleMutationResult;
  stopSensor: StopSensorMutationResultOrError;
  terminatePipelineExecution: TerminateRunResult;
  terminateRun: TerminateRunResult;
  terminateRuns: TerminateRunsResultOrError;
  wipeAssets: AssetWipeMutationResult;
};

export type MutationAddDynamicPartitionArgs = {
  partitionKey: Scalars['String']['input'];
  partitionsDefName: Scalars['String']['input'];
  repositorySelector: RepositorySelector;
};

export type MutationCancelPartitionBackfillArgs = {
  backfillId: Scalars['String']['input'];
};

export type MutationDeleteConcurrencyLimitArgs = {
  concurrencyKey: Scalars['String']['input'];
};

export type MutationDeleteDynamicPartitionsArgs = {
  partitionKeys: Array<Scalars['String']['input']>;
  partitionsDefName: Scalars['String']['input'];
  repositorySelector: RepositorySelector;
};

export type MutationDeletePipelineRunArgs = {
  runId: Scalars['String']['input'];
};

export type MutationDeleteRunArgs = {
  runId: Scalars['String']['input'];
};

export type MutationFreeConcurrencySlotsArgs = {
  runId: Scalars['String']['input'];
  stepKey?: InputMaybe<Scalars['String']['input']>;
};

export type MutationFreeConcurrencySlotsForRunArgs = {
  runId: Scalars['String']['input'];
};

export type MutationLaunchMultipleRunsArgs = {
  executionParamsList: Array<ExecutionParams>;
};

export type MutationLaunchPartitionBackfillArgs = {
  backfillParams: LaunchBackfillParams;
};

export type MutationLaunchPipelineExecutionArgs = {
  executionParams: ExecutionParams;
};

export type MutationLaunchPipelineReexecutionArgs = {
  executionParams?: InputMaybe<ExecutionParams>;
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

export type MutationLaunchRunArgs = {
  executionParams: ExecutionParams;
};

export type MutationLaunchRunReexecutionArgs = {
  executionParams?: InputMaybe<ExecutionParams>;
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

export type MutationLogTelemetryArgs = {
  action: Scalars['String']['input'];
  clientId: Scalars['String']['input'];
  clientTime: Scalars['String']['input'];
  metadata: Scalars['String']['input'];
};

export type MutationReexecutePartitionBackfillArgs = {
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

export type MutationReloadRepositoryLocationArgs = {
  repositoryLocationName: Scalars['String']['input'];
};

export type MutationReportAssetCheckEvaluationArgs = {
  eventParams: ReportAssetCheckEvaluationParams;
};

export type MutationReportRunlessAssetEventsArgs = {
  eventParams: ReportRunlessAssetEventsParams;
};

export type MutationResetScheduleArgs = {
  scheduleSelector: ScheduleSelector;
};

export type MutationResetSensorArgs = {
  sensorSelector: SensorSelector;
};

export type MutationResumePartitionBackfillArgs = {
  backfillId: Scalars['String']['input'];
};

export type MutationScheduleDryRunArgs = {
  selectorData: ScheduleSelector;
  timestamp?: InputMaybe<Scalars['Float']['input']>;
};

export type MutationSensorDryRunArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  selectorData: SensorSelector;
};

export type MutationSetAutoMaterializePausedArgs = {
  paused: Scalars['Boolean']['input'];
};

export type MutationSetConcurrencyLimitArgs = {
  concurrencyKey: Scalars['String']['input'];
  limit: Scalars['Int']['input'];
};

export type MutationSetSensorCursorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  sensorSelector: SensorSelector;
};

export type MutationShutdownRepositoryLocationArgs = {
  repositoryLocationName: Scalars['String']['input'];
};

export type MutationStartScheduleArgs = {
  scheduleSelector: ScheduleSelector;
};

export type MutationStartSensorArgs = {
  sensorSelector: SensorSelector;
};

export type MutationStopRunningScheduleArgs = {
  id?: InputMaybe<Scalars['String']['input']>;
  scheduleOriginId?: InputMaybe<Scalars['String']['input']>;
  scheduleSelectorId?: InputMaybe<Scalars['String']['input']>;
};

export type MutationStopSensorArgs = {
  id?: InputMaybe<Scalars['String']['input']>;
  jobOriginId?: InputMaybe<Scalars['String']['input']>;
  jobSelectorId?: InputMaybe<Scalars['String']['input']>;
};

export type MutationTerminatePipelineExecutionArgs = {
  runId: Scalars['String']['input'];
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

export type MutationTerminateRunArgs = {
  runId: Scalars['String']['input'];
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

export type MutationTerminateRunsArgs = {
  runIds: Array<Scalars['String']['input']>;
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

export type MutationWipeAssetsArgs = {
  assetPartitionRanges: Array<PartitionsByAssetSelector>;
};

export type NestedResourceEntry = {
  __typename: 'NestedResourceEntry';
  name: Scalars['String']['output'];
  resource: Maybe<ResourceDetails>;
  type: NestedResourceType;
};

export {NestedResourceType};

export type NoModeProvidedError = Error & {
  __typename: 'NoModeProvidedError';
  message: Scalars['String']['output'];
  pipelineName: Scalars['String']['output'];
};

export type NodeInvocationSite = {
  __typename: 'NodeInvocationSite';
  pipeline: Pipeline;
  solidHandle: SolidHandle;
};

export type NotebookMetadataEntry = MetadataEntry & {
  __typename: 'NotebookMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  path: Scalars['String']['output'];
};

export type NullMetadataEntry = MetadataEntry & {
  __typename: 'NullMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
};

export type NullableConfigType = ConfigType &
  WrappingConfigType & {
    __typename: 'NullableConfigType';
    description: Maybe<Scalars['String']['output']>;
    isSelector: Scalars['Boolean']['output'];
    key: Scalars['String']['output'];
    ofType:
      | ArrayConfigType
      | CompositeConfigType
      | EnumConfigType
      | MapConfigType
      | NullableConfigType
      | RegularConfigType
      | ScalarUnionConfigType;
    recursiveConfigTypes: Array<
      | ArrayConfigType
      | CompositeConfigType
      | EnumConfigType
      | MapConfigType
      | NullableConfigType
      | RegularConfigType
      | ScalarUnionConfigType
    >;
    typeParamKeys: Array<Scalars['String']['output']>;
  };

export type NullableDagsterType = DagsterType &
  WrappingDagsterType & {
    __typename: 'NullableDagsterType';
    description: Maybe<Scalars['String']['output']>;
    displayName: Scalars['String']['output'];
    innerTypes: Array<ListDagsterType | NullableDagsterType | RegularDagsterType>;
    inputSchemaType: Maybe<
      | ArrayConfigType
      | CompositeConfigType
      | EnumConfigType
      | MapConfigType
      | NullableConfigType
      | RegularConfigType
      | ScalarUnionConfigType
    >;
    isBuiltin: Scalars['Boolean']['output'];
    isList: Scalars['Boolean']['output'];
    isNothing: Scalars['Boolean']['output'];
    isNullable: Scalars['Boolean']['output'];
    key: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    name: Maybe<Scalars['String']['output']>;
    ofType: ListDagsterType | NullableDagsterType | RegularDagsterType;
    outputSchemaType: Maybe<
      | ArrayConfigType
      | CompositeConfigType
      | EnumConfigType
      | MapConfigType
      | NullableConfigType
      | RegularConfigType
      | ScalarUnionConfigType
    >;
  };

export type ObjectStoreOperationEvent = MessageEvent &
  StepEvent & {
    __typename: 'ObjectStoreOperationEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    operationResult: ObjectStoreOperationResult;
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ObjectStoreOperationResult = DisplayableEvent & {
  __typename: 'ObjectStoreOperationResult';
  description: Maybe<Scalars['String']['output']>;
  label: Maybe<Scalars['String']['output']>;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  op: ObjectStoreOperationType;
};

export {ObjectStoreOperationType};

export type ObservationEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ObservationEvent';
    assetKey: Maybe<AssetKey>;
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    partition: Maybe<Scalars['String']['output']>;
    runId: Scalars['String']['output'];
    runOrError: RunOrError;
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    stepStats: RunStepStats;
    tags: Array<EventTag>;
    timestamp: Scalars['String']['output'];
  };

export type Output = {
  __typename: 'Output';
  definition: OutputDefinition;
  dependedBy: Array<Input>;
  solid: Solid;
};

export type OutputDefinition = {
  __typename: 'OutputDefinition';
  description: Maybe<Scalars['String']['output']>;
  isDynamic: Maybe<Scalars['Boolean']['output']>;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  name: Scalars['String']['output'];
  type: ListDagsterType | NullableDagsterType | RegularDagsterType;
};

export type OutputMapping = {
  __typename: 'OutputMapping';
  definition: OutputDefinition;
  mappedOutput: Output;
};

export type ParentMaterializedRuleEvaluationData = {
  __typename: 'ParentMaterializedRuleEvaluationData';
  updatedAssetKeys: Maybe<Array<AssetKey>>;
  willUpdateAssetKeys: Maybe<Array<AssetKey>>;
};

export type Partition = {
  __typename: 'Partition';
  mode: Scalars['String']['output'];
  name: Scalars['String']['output'];
  partitionSetName: Scalars['String']['output'];
  runConfigOrError: PartitionRunConfigOrError;
  runs: Array<Run>;
  solidSelection: Maybe<Array<Scalars['String']['output']>>;
  status: Maybe<RunStatus>;
  tagsOrError: PartitionTagsOrError;
};

export type PartitionRunsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type PartitionBackfill = RunsFeedEntry & {
  __typename: 'PartitionBackfill';
  assetBackfillData: Maybe<AssetBackfillData>;
  assetCheckSelection: Maybe<Array<AssetCheckhandle>>;
  assetSelection: Maybe<Array<AssetKey>>;
  cancelableRuns: Array<Run>;
  creationTime: Scalars['Float']['output'];
  description: Maybe<Scalars['String']['output']>;
  endTime: Maybe<Scalars['Float']['output']>;
  endTimestamp: Maybe<Scalars['Float']['output']>;
  error: Maybe<PythonError>;
  fromFailure: Scalars['Boolean']['output'];
  hasCancelPermission: Scalars['Boolean']['output'];
  hasResumePermission: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  isAssetBackfill: Scalars['Boolean']['output'];
  isValidSerialization: Scalars['Boolean']['output'];
  jobName: Maybe<Scalars['String']['output']>;
  logEvents: InstigationEventConnection;
  numCancelable: Scalars['Int']['output'];
  numPartitions: Maybe<Scalars['Int']['output']>;
  partitionNames: Maybe<Array<Scalars['String']['output']>>;
  partitionSet: Maybe<PartitionSet>;
  partitionSetName: Maybe<Scalars['String']['output']>;
  partitionStatusCounts: Array<PartitionStatusCounts>;
  partitionStatuses: Maybe<PartitionStatuses>;
  partitionsTargetedForAssetKey: Maybe<AssetBackfillTargetPartitions>;
  reexecutionSteps: Maybe<Array<Scalars['String']['output']>>;
  runStatus: RunStatus;
  runs: Array<Run>;
  startTime: Maybe<Scalars['Float']['output']>;
  status: BulkActionStatus;
  tags: Array<PipelineTag>;
  timestamp: Scalars['Float']['output'];
  title: Maybe<Scalars['String']['output']>;
  unfinishedRuns: Array<Run>;
  user: Maybe<Scalars['String']['output']>;
};

export type PartitionBackfillCancelableRunsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type PartitionBackfillLogEventsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
};

export type PartitionBackfillPartitionsTargetedForAssetKeyArgs = {
  assetKey?: InputMaybe<AssetKeyInput>;
};

export type PartitionBackfillRunsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type PartitionBackfillUnfinishedRunsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type PartitionBackfillOrError = BackfillNotFoundError | PartitionBackfill | PythonError;

export type PartitionBackfills = {
  __typename: 'PartitionBackfills';
  results: Array<PartitionBackfill>;
};

export type PartitionBackfillsOrError = PartitionBackfills | PythonError;

export type PartitionDefinition = {
  __typename: 'PartitionDefinition';
  description: Scalars['String']['output'];
  dimensionTypes: Array<DimensionDefinitionType>;
  fmt: Maybe<Scalars['String']['output']>;
  name: Maybe<Scalars['String']['output']>;
  type: PartitionDefinitionType;
};

export {PartitionDefinitionType};

export type PartitionKeyConnection = {
  __typename: 'PartitionKeyConnection';
  cursor: Scalars['String']['output'];
  hasMore: Scalars['Boolean']['output'];
  results: Array<Scalars['String']['output']>;
};

export type PartitionKeyRange = {
  __typename: 'PartitionKeyRange';
  end: Scalars['String']['output'];
  start: Scalars['String']['output'];
};

export type PartitionKeys = {
  __typename: 'PartitionKeys';
  partitionKeys: Array<Scalars['String']['output']>;
};

export type PartitionKeysNotFoundError = Error & {
  __typename: 'PartitionKeysNotFoundError';
  message: Scalars['String']['output'];
  partitionKeys: Array<Scalars['String']['output']>;
};

export type PartitionKeysOrError = PartitionKeys | PartitionSubsetDeserializationError;

export type PartitionMapping = {
  __typename: 'PartitionMapping';
  className: Scalars['String']['output'];
  description: Scalars['String']['output'];
};

export type PartitionRange = {
  __typename: 'PartitionRange';
  end: Scalars['String']['output'];
  start: Scalars['String']['output'];
};

export type PartitionRangeSelector = {
  end: Scalars['String']['input'];
  start: Scalars['String']['input'];
};

export {PartitionRangeStatus};

export type PartitionRun = {
  __typename: 'PartitionRun';
  id: Scalars['String']['output'];
  partitionName: Scalars['String']['output'];
  run: Maybe<Run>;
};

export type PartitionRunConfig = {
  __typename: 'PartitionRunConfig';
  yaml: Scalars['String']['output'];
};

export type PartitionRunConfigOrError = PartitionRunConfig | PythonError;

export type PartitionSet = {
  __typename: 'PartitionSet';
  backfills: Array<PartitionBackfill>;
  hasCancelBackfillPermission: Scalars['Boolean']['output'];
  hasLaunchBackfillPermission: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  mode: Scalars['String']['output'];
  name: Scalars['String']['output'];
  partition: Maybe<Partition>;
  partitionRuns: Array<PartitionRun>;
  partitionStatusesOrError: PartitionStatusesOrError;
  partitionsOrError: PartitionsOrError;
  pipelineName: Scalars['String']['output'];
  repositoryOrigin: RepositoryOrigin;
  solidSelection: Maybe<Array<Scalars['String']['output']>>;
};

export type PartitionSetBackfillsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type PartitionSetPartitionArgs = {
  partitionName: Scalars['String']['input'];
};

export type PartitionSetPartitionsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  reverse?: InputMaybe<Scalars['Boolean']['input']>;
};

export type PartitionSetNotFoundError = Error & {
  __typename: 'PartitionSetNotFoundError';
  message: Scalars['String']['output'];
  partitionSetName: Scalars['String']['output'];
};

export type PartitionSetOrError = PartitionSet | PartitionSetNotFoundError | PythonError;

export type PartitionSetSelector = {
  partitionSetName: Scalars['String']['input'];
  repositorySelector: RepositorySelector;
};

export type PartitionSets = {
  __typename: 'PartitionSets';
  results: Array<PartitionSet>;
};

export type PartitionSetsOrError = PartitionSets | PipelineNotFoundError | PythonError;

export type PartitionStats = {
  __typename: 'PartitionStats';
  numFailed: Scalars['Int']['output'];
  numMaterialized: Scalars['Int']['output'];
  numMaterializing: Scalars['Int']['output'];
  numPartitions: Scalars['Int']['output'];
};

export type PartitionStatus = {
  __typename: 'PartitionStatus';
  id: Scalars['String']['output'];
  partitionName: Scalars['String']['output'];
  runDuration: Maybe<Scalars['Float']['output']>;
  runId: Maybe<Scalars['String']['output']>;
  runStatus: Maybe<RunStatus>;
};

export type PartitionStatus1D = DefaultPartitionStatuses | TimePartitionStatuses;

export type PartitionStatusCounts = {
  __typename: 'PartitionStatusCounts';
  count: Scalars['Int']['output'];
  runStatus: RunStatus;
};

export type PartitionStatuses = {
  __typename: 'PartitionStatuses';
  results: Array<PartitionStatus>;
};

export type PartitionStatusesOrError = PartitionStatuses | PythonError;

export type PartitionSubsetDeserializationError = Error & {
  __typename: 'PartitionSubsetDeserializationError';
  message: Scalars['String']['output'];
};

export type PartitionTags = {
  __typename: 'PartitionTags';
  results: Array<PipelineTag>;
};

export type PartitionTagsAndConfig = {
  __typename: 'PartitionTagsAndConfig';
  jobName: Scalars['String']['output'];
  name: Scalars['String']['output'];
  runConfigOrError: PartitionRunConfigOrError;
  tagsOrError: PartitionTagsOrError;
};

export type PartitionTagsOrError = PartitionTags | PythonError;

export type PartitionedAssetConditionEvaluationNode = {
  __typename: 'PartitionedAssetConditionEvaluationNode';
  childUniqueIds: Array<Scalars['String']['output']>;
  description: Scalars['String']['output'];
  endTimestamp: Maybe<Scalars['Float']['output']>;
  entityKey: EntityKey;
  numCandidates: Maybe<Scalars['Int']['output']>;
  numTrue: Maybe<Scalars['Int']['output']>;
  startTimestamp: Maybe<Scalars['Float']['output']>;
  uniqueId: Scalars['String']['output'];
};

export type Partitions = {
  __typename: 'Partitions';
  results: Array<Partition>;
};

export type PartitionsByAssetSelector = {
  assetKey: AssetKeyInput;
  partitions?: InputMaybe<PartitionsSelector>;
};

export type PartitionsOrError = Partitions | PythonError;

export type PartitionsSelector = {
  range?: InputMaybe<PartitionRangeSelector>;
  ranges?: InputMaybe<Array<PartitionRangeSelector>>;
};

export type PathMetadataEntry = MetadataEntry & {
  __typename: 'PathMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  path: Scalars['String']['output'];
};

export type PendingConcurrencyStep = {
  __typename: 'PendingConcurrencyStep';
  assignedTimestamp: Maybe<Scalars['Float']['output']>;
  enqueuedTimestamp: Scalars['Float']['output'];
  priority: Maybe<Scalars['Int']['output']>;
  runId: Scalars['String']['output'];
  stepKey: Scalars['String']['output'];
};

export type Permission = {
  __typename: 'Permission';
  disabledReason: Maybe<Scalars['String']['output']>;
  permission: Scalars['String']['output'];
  value: Scalars['Boolean']['output'];
};

export type Pipeline = IPipelineSnapshot &
  SolidContainer & {
    __typename: 'Pipeline';
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<ListDagsterType | NullableDagsterType | RegularDagsterType>;
    description: Maybe<Scalars['String']['output']>;
    externalJobSource: Maybe<Scalars['String']['output']>;
    graphName: Scalars['String']['output'];
    hasLaunchExecutionPermission: Scalars['Boolean']['output'];
    hasLaunchReexecutionPermission: Scalars['Boolean']['output'];
    id: Scalars['ID']['output'];
    isAssetJob: Scalars['Boolean']['output'];
    isJob: Scalars['Boolean']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    modes: Array<Mode>;
    name: Scalars['String']['output'];
    nodeNames: Array<Scalars['String']['output']>;
    owners: Array<DefinitionOwner>;
    parentSnapshotId: Maybe<Scalars['String']['output']>;
    partition: Maybe<PartitionTagsAndConfig>;
    partitionKeysOrError: PartitionKeys;
    pipelineSnapshotId: Scalars['String']['output'];
    presets: Array<PipelinePreset>;
    repository: Repository;
    runTags: Array<PipelineTag>;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type PipelineDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String']['input'];
};

export type PipelinePartitionArgs = {
  partitionName: Scalars['String']['input'];
  selectedAssetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type PipelinePartitionKeysOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  reverse?: InputMaybe<Scalars['Boolean']['input']>;
  selectedAssetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type PipelineRunsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type PipelineSolidHandleArgs = {
  handleID: Scalars['String']['input'];
};

export type PipelineSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']['input']>;
};

export type PipelineConfigValidationError = {
  message: Scalars['String']['output'];
  path: Array<Scalars['String']['output']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type PipelineConfigValidationInvalid = {
  errors: Array<
    | FieldNotDefinedConfigError
    | FieldsNotDefinedConfigError
    | MissingFieldConfigError
    | MissingFieldsConfigError
    | RuntimeMismatchConfigError
    | SelectorTypeConfigError
  >;
  pipelineName: Scalars['String']['output'];
};

export type PipelineConfigValidationResult =
  | InvalidSubsetError
  | PipelineConfigValidationValid
  | PipelineNotFoundError
  | PythonError
  | RunConfigValidationInvalid;

export type PipelineConfigValidationValid = {
  __typename: 'PipelineConfigValidationValid';
  pipelineName: Scalars['String']['output'];
};

export type PipelineNotFoundError = Error & {
  __typename: 'PipelineNotFoundError';
  message: Scalars['String']['output'];
  pipelineName: Scalars['String']['output'];
  repositoryLocationName: Scalars['String']['output'];
  repositoryName: Scalars['String']['output'];
};

export type PipelineOrError = InvalidSubsetError | Pipeline | PipelineNotFoundError | PythonError;

export type PipelinePreset = {
  __typename: 'PipelinePreset';
  mode: Scalars['String']['output'];
  name: Scalars['String']['output'];
  runConfigYaml: Scalars['String']['output'];
  solidSelection: Maybe<Array<Scalars['String']['output']>>;
  tags: Array<PipelineTag>;
};

export type PipelineReference = {
  name: Scalars['String']['output'];
  solidSelection: Maybe<Array<Scalars['String']['output']>>;
};

export type PipelineRun = {
  assets: Array<Asset>;
  canTerminate: Scalars['Boolean']['output'];
  capturedLogs: CapturedLogs;
  eventConnection: EventConnection;
  executionPlan: Maybe<ExecutionPlan>;
  id: Scalars['ID']['output'];
  jobName: Scalars['String']['output'];
  mode: Scalars['String']['output'];
  parentRunId: Maybe<Scalars['String']['output']>;
  pipeline: PipelineSnapshot | UnknownPipeline;
  pipelineName: Scalars['String']['output'];
  pipelineSnapshotId: Maybe<Scalars['String']['output']>;
  repositoryOrigin: Maybe<RepositoryOrigin>;
  rootRunId: Maybe<Scalars['String']['output']>;
  runConfig: Scalars['RunConfigData']['output'];
  runConfigYaml: Scalars['String']['output'];
  runId: Scalars['String']['output'];
  solidSelection: Maybe<Array<Scalars['String']['output']>>;
  stats: RunStatsSnapshotOrError;
  status: RunStatus;
  stepKeysToExecute: Maybe<Array<Scalars['String']['output']>>;
  stepStats: Array<RunStepStats>;
  tags: Array<PipelineTag>;
};

export type PipelineRunCapturedLogsArgs = {
  fileKey: Scalars['String']['input'];
};

export type PipelineRunEventConnectionArgs = {
  afterCursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type PipelineRunConflict = {
  message: Scalars['String']['output'];
};

export type PipelineRunLogsSubscriptionFailure = {
  __typename: 'PipelineRunLogsSubscriptionFailure';
  message: Scalars['String']['output'];
  missingRunId: Maybe<Scalars['String']['output']>;
};

export type PipelineRunLogsSubscriptionPayload =
  | PipelineRunLogsSubscriptionFailure
  | PipelineRunLogsSubscriptionSuccess;

export type PipelineRunLogsSubscriptionSuccess = {
  __typename: 'PipelineRunLogsSubscriptionSuccess';
  cursor: Scalars['String']['output'];
  hasMorePastEvents: Scalars['Boolean']['output'];
  messages: Array<DagsterRunEvent>;
  run: Run;
};

export type PipelineRunMetadataEntry = MetadataEntry & {
  __typename: 'PipelineRunMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  runId: Scalars['String']['output'];
};

export type PipelineRunNotFoundError = {
  message: Scalars['String']['output'];
  runId: Scalars['String']['output'];
};

export type PipelineRunStatsSnapshot = {
  endTime: Maybe<Scalars['Float']['output']>;
  enqueuedTime: Maybe<Scalars['Float']['output']>;
  expectations: Scalars['Int']['output'];
  id: Scalars['String']['output'];
  launchTime: Maybe<Scalars['Float']['output']>;
  materializations: Scalars['Int']['output'];
  runId: Scalars['String']['output'];
  startTime: Maybe<Scalars['Float']['output']>;
  stepsFailed: Scalars['Int']['output'];
  stepsSucceeded: Scalars['Int']['output'];
};

export type PipelineRunStepStats = {
  endTime: Maybe<Scalars['Float']['output']>;
  expectationResults: Array<ExpectationResult>;
  materializations: Array<MaterializationEvent>;
  runId: Scalars['String']['output'];
  startTime: Maybe<Scalars['Float']['output']>;
  status: Maybe<StepEventStatus>;
  stepKey: Scalars['String']['output'];
};

export type PipelineRuns = {
  count: Maybe<Scalars['Int']['output']>;
  results: Array<Run>;
};

export type PipelineSelector = {
  assetCheckSelection?: InputMaybe<Array<AssetCheckHandleInput>>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  pipelineName: Scalars['String']['input'];
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  solidSelection?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type PipelineSnapshot = IPipelineSnapshot &
  PipelineReference &
  SolidContainer & {
    __typename: 'PipelineSnapshot';
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<ListDagsterType | NullableDagsterType | RegularDagsterType>;
    description: Maybe<Scalars['String']['output']>;
    externalJobSource: Maybe<Scalars['String']['output']>;
    graphName: Scalars['String']['output'];
    id: Scalars['ID']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    modes: Array<Mode>;
    name: Scalars['String']['output'];
    owners: Array<DefinitionOwner>;
    parentSnapshotId: Maybe<Scalars['String']['output']>;
    pipelineSnapshotId: Scalars['String']['output'];
    runTags: Array<PipelineTag>;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solidSelection: Maybe<Array<Scalars['String']['output']>>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type PipelineSnapshotDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars['String']['input'];
};

export type PipelineSnapshotRunsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type PipelineSnapshotSolidHandleArgs = {
  handleID: Scalars['String']['input'];
};

export type PipelineSnapshotSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']['input']>;
};

export type PipelineSnapshotNotFoundError = Error & {
  __typename: 'PipelineSnapshotNotFoundError';
  message: Scalars['String']['output'];
  snapshotId: Scalars['String']['output'];
};

export type PipelineSnapshotOrError =
  | PipelineNotFoundError
  | PipelineSnapshot
  | PipelineSnapshotNotFoundError
  | PythonError;

export type PipelineTag = {
  __typename: 'PipelineTag';
  key: Scalars['String']['output'];
  value: Scalars['String']['output'];
};

export type PipelineTagAndValues = {
  __typename: 'PipelineTagAndValues';
  key: Scalars['String']['output'];
  values: Array<Scalars['String']['output']>;
};

export type PoolConfig = {
  __typename: 'PoolConfig';
  defaultPoolLimit: Maybe<Scalars['Int']['output']>;
  opGranularityRunBuffer: Maybe<Scalars['Int']['output']>;
  poolGranularity: Maybe<Scalars['String']['output']>;
};

export type PoolMetadataEntry = MetadataEntry & {
  __typename: 'PoolMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  pool: Scalars['String']['output'];
};

export type PresetNotFoundError = Error & {
  __typename: 'PresetNotFoundError';
  message: Scalars['String']['output'];
  preset: Scalars['String']['output'];
};

export type PythonArtifactMetadataEntry = MetadataEntry & {
  __typename: 'PythonArtifactMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  module: Scalars['String']['output'];
  name: Scalars['String']['output'];
};

export type PythonError = Error & {
  __typename: 'PythonError';
  cause: Maybe<PythonError>;
  causes: Array<PythonError>;
  className: Maybe<Scalars['String']['output']>;
  errorChain: Array<ErrorChainLink>;
  message: Scalars['String']['output'];
  stack: Array<Scalars['String']['output']>;
};

export type Query = {
  __typename: 'Query';
  allTopLevelResourceDetailsOrError: ResourceDetailsListOrError;
  assetBackfillPreview: Array<AssetPartitions>;
  assetCheckExecutions: Array<AssetCheckExecution>;
  assetConditionEvaluationForPartition: Maybe<AssetConditionEvaluation>;
  assetConditionEvaluationRecordsOrError: Maybe<AssetConditionEvaluationRecordsOrError>;
  assetConditionEvaluationsForEvaluationId: Maybe<AssetConditionEvaluationRecordsOrError>;
  assetNodeAdditionalRequiredKeys: Array<AssetKey>;
  assetNodeDefinitionCollisions: Array<AssetNodeDefinitionCollision>;
  assetNodeOrError: AssetNodeOrError;
  assetNodes: Array<AssetNode>;
  assetOrError: AssetOrError;
  assetRecordsOrError: AssetRecordsOrError;
  assetsLatestInfo: Array<AssetLatestInfo>;
  assetsOrError: AssetsOrError;
  autoMaterializeAssetEvaluationsOrError: Maybe<AutoMaterializeAssetEvaluationRecordsOrError>;
  autoMaterializeEvaluationsForEvaluationId: Maybe<AutoMaterializeAssetEvaluationRecordsOrError>;
  autoMaterializeTicks: Array<InstigationTick>;
  canBulkTerminate: Scalars['Boolean']['output'];
  capturedLogs: CapturedLogs;
  capturedLogsMetadata: CapturedLogsMetadata;
  executionPlanOrError: ExecutionPlanOrError;
  graphOrError: GraphOrError;
  instance: Instance;
  instigationStateOrError: InstigationStateOrError;
  instigationStatesOrError: InstigationStatesOrError;
  isPipelineConfigValid: PipelineConfigValidationResult;
  latestDefsStateInfo: Maybe<DefsStateInfo>;
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
  resourcesOrError: ResourcesOrError;
  runConfigSchemaOrError: RunConfigSchemaOrError;
  runGroupOrError: RunGroupOrError;
  runIdsOrError: RunIdsOrError;
  runOrError: RunOrError;
  runTagKeysOrError: Maybe<RunTagKeysOrError>;
  runTagsOrError: Maybe<RunTagsOrError>;
  runsFeedCountOrError: RunsFeedCountOrError;
  runsFeedOrError: RunsFeedConnectionOrError;
  runsOrError: RunsOrError;
  scheduleOrError: ScheduleOrError;
  scheduler: SchedulerOrError;
  schedulesOrError: SchedulesOrError;
  sensorOrError: SensorOrError;
  sensorsOrError: SensorsOrError;
  shouldShowNux: Scalars['Boolean']['output'];
  test: Maybe<TestFields>;
  topLevelResourceDetailsOrError: ResourceDetailsOrError;
  truePartitionsForAutomationConditionEvaluationNode: Array<Scalars['String']['output']>;
  utilizedEnvVarsOrError: EnvVarWithConsumersOrError;
  version: Scalars['String']['output'];
  workspaceLocationEntryOrError: Maybe<WorkspaceLocationEntryOrError>;
  workspaceOrError: WorkspaceOrError;
};

export type QueryAllTopLevelResourceDetailsOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type QueryAssetBackfillPreviewArgs = {
  params: AssetBackfillPreviewParams;
};

export type QueryAssetCheckExecutionsArgs = {
  assetKey: AssetKeyInput;
  checkName: Scalars['String']['input'];
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit: Scalars['Int']['input'];
  partition?: InputMaybe<Scalars['String']['input']>;
};

export type QueryAssetConditionEvaluationForPartitionArgs = {
  assetKey?: InputMaybe<AssetKeyInput>;
  evaluationId: Scalars['ID']['input'];
  partition: Scalars['String']['input'];
};

export type QueryAssetConditionEvaluationRecordsOrErrorArgs = {
  assetCheckKey?: InputMaybe<AssetCheckHandleInput>;
  assetKey?: InputMaybe<AssetKeyInput>;
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit: Scalars['Int']['input'];
};

export type QueryAssetConditionEvaluationsForEvaluationIdArgs = {
  evaluationId: Scalars['ID']['input'];
};

export type QueryAssetNodeAdditionalRequiredKeysArgs = {
  assetKeys: Array<AssetKeyInput>;
};

export type QueryAssetNodeDefinitionCollisionsArgs = {
  assetKeys: Array<AssetKeyInput>;
};

export type QueryAssetNodeOrErrorArgs = {
  assetKey: AssetKeyInput;
};

export type QueryAssetNodesArgs = {
  assetKeys?: InputMaybe<Array<AssetKeyInput>>;
  group?: InputMaybe<AssetGroupSelector>;
  loadMaterializations?: InputMaybe<Scalars['Boolean']['input']>;
  pipeline?: InputMaybe<PipelineSelector>;
};

export type QueryAssetOrErrorArgs = {
  assetKey: AssetKeyInput;
};

export type QueryAssetRecordsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  prefix?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type QueryAssetsLatestInfoArgs = {
  assetKeys: Array<AssetKeyInput>;
};

export type QueryAssetsOrErrorArgs = {
  assetKeys?: InputMaybe<Array<AssetKeyInput>>;
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  prefix?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type QueryAutoMaterializeAssetEvaluationsOrErrorArgs = {
  assetKey: AssetKeyInput;
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit: Scalars['Int']['input'];
};

export type QueryAutoMaterializeEvaluationsForEvaluationIdArgs = {
  evaluationId: Scalars['ID']['input'];
};

export type QueryAutoMaterializeTicksArgs = {
  afterTimestamp?: InputMaybe<Scalars['Float']['input']>;
  beforeTimestamp?: InputMaybe<Scalars['Float']['input']>;
  cursor?: InputMaybe<Scalars['String']['input']>;
  dayOffset?: InputMaybe<Scalars['Int']['input']>;
  dayRange?: InputMaybe<Scalars['Int']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  statuses?: InputMaybe<Array<InstigationTickStatus>>;
};

export type QueryCapturedLogsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  logKey: Array<Scalars['String']['input']>;
};

export type QueryCapturedLogsMetadataArgs = {
  logKey: Array<Scalars['String']['input']>;
};

export type QueryExecutionPlanOrErrorArgs = {
  mode: Scalars['String']['input'];
  pipeline: PipelineSelector;
  runConfigData?: InputMaybe<Scalars['RunConfigData']['input']>;
};

export type QueryGraphOrErrorArgs = {
  selector?: InputMaybe<GraphSelector>;
};

export type QueryInstigationStateOrErrorArgs = {
  id?: InputMaybe<Scalars['String']['input']>;
  instigationSelector: InstigationSelector;
};

export type QueryInstigationStatesOrErrorArgs = {
  repositoryID: Scalars['String']['input'];
};

export type QueryIsPipelineConfigValidArgs = {
  mode: Scalars['String']['input'];
  pipeline: PipelineSelector;
  runConfigData?: InputMaybe<Scalars['RunConfigData']['input']>;
};

export type QueryLogsForRunArgs = {
  afterCursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  runId: Scalars['ID']['input'];
};

export type QueryPartitionBackfillOrErrorArgs = {
  backfillId: Scalars['String']['input'];
};

export type QueryPartitionBackfillsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  filters?: InputMaybe<BulkActionsFilter>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  status?: InputMaybe<BulkActionStatus>;
};

export type QueryPartitionSetOrErrorArgs = {
  partitionSetName?: InputMaybe<Scalars['String']['input']>;
  repositorySelector: RepositorySelector;
};

export type QueryPartitionSetsOrErrorArgs = {
  pipelineName: Scalars['String']['input'];
  repositorySelector: RepositorySelector;
};

export type QueryPipelineOrErrorArgs = {
  params: PipelineSelector;
};

export type QueryPipelineRunOrErrorArgs = {
  runId: Scalars['ID']['input'];
};

export type QueryPipelineRunsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type QueryPipelineSnapshotOrErrorArgs = {
  activePipelineSelector?: InputMaybe<PipelineSelector>;
  snapshotId?: InputMaybe<Scalars['String']['input']>;
};

export type QueryRepositoriesOrErrorArgs = {
  repositorySelector?: InputMaybe<RepositorySelector>;
};

export type QueryRepositoryOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type QueryResourcesOrErrorArgs = {
  pipelineSelector: PipelineSelector;
};

export type QueryRunConfigSchemaOrErrorArgs = {
  mode?: InputMaybe<Scalars['String']['input']>;
  selector: PipelineSelector;
};

export type QueryRunGroupOrErrorArgs = {
  runId: Scalars['ID']['input'];
};

export type QueryRunIdsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type QueryRunOrErrorArgs = {
  runId: Scalars['ID']['input'];
};

export type QueryRunTagsOrErrorArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  tagKeys?: InputMaybe<Array<Scalars['String']['input']>>;
  valuePrefix?: InputMaybe<Scalars['String']['input']>;
};

export type QueryRunsFeedCountOrErrorArgs = {
  filter?: InputMaybe<RunsFilter>;
  view: RunsFeedView;
};

export type QueryRunsFeedOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<RunsFilter>;
  limit: Scalars['Int']['input'];
  view: RunsFeedView;
};

export type QueryRunsOrErrorArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type QueryScheduleOrErrorArgs = {
  scheduleSelector: ScheduleSelector;
};

export type QuerySchedulesOrErrorArgs = {
  repositorySelector: RepositorySelector;
  scheduleStatus?: InputMaybe<InstigationStatus>;
};

export type QuerySensorOrErrorArgs = {
  sensorSelector: SensorSelector;
};

export type QuerySensorsOrErrorArgs = {
  repositorySelector: RepositorySelector;
  sensorStatus?: InputMaybe<InstigationStatus>;
};

export type QueryTopLevelResourceDetailsOrErrorArgs = {
  resourceSelector: ResourceSelector;
};

export type QueryTruePartitionsForAutomationConditionEvaluationNodeArgs = {
  assetKey?: InputMaybe<AssetKeyInput>;
  evaluationId: Scalars['ID']['input'];
  nodeUniqueId?: InputMaybe<Scalars['String']['input']>;
};

export type QueryUtilizedEnvVarsOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

export type QueryWorkspaceLocationEntryOrErrorArgs = {
  name: Scalars['String']['input'];
};

export type ReexecutionParams = {
  extraTags?: InputMaybe<Array<ExecutionTag>>;
  parentRunId: Scalars['String']['input'];
  strategy: ReexecutionStrategy;
  useParentRunTags?: InputMaybe<Scalars['Boolean']['input']>;
};

export {ReexecutionStrategy};

export type RegularConfigType = ConfigType & {
  __typename: 'RegularConfigType';
  description: Maybe<Scalars['String']['output']>;
  givenName: Scalars['String']['output'];
  isSelector: Scalars['Boolean']['output'];
  key: Scalars['String']['output'];
  recursiveConfigTypes: Array<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
  typeParamKeys: Array<Scalars['String']['output']>;
};

export type RegularDagsterType = DagsterType & {
  __typename: 'RegularDagsterType';
  description: Maybe<Scalars['String']['output']>;
  displayName: Scalars['String']['output'];
  innerTypes: Array<ListDagsterType | NullableDagsterType | RegularDagsterType>;
  inputSchemaType: Maybe<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
  isBuiltin: Scalars['Boolean']['output'];
  isList: Scalars['Boolean']['output'];
  isNothing: Scalars['Boolean']['output'];
  isNullable: Scalars['Boolean']['output'];
  key: Scalars['String']['output'];
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  name: Maybe<Scalars['String']['output']>;
  outputSchemaType: Maybe<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
};

export type ReloadNotSupported = Error & {
  __typename: 'ReloadNotSupported';
  message: Scalars['String']['output'];
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

export type ReportAssetCheckEvaluationParams = {
  assetKey: AssetKeyInput;
  checkName: Scalars['String']['input'];
  partition?: InputMaybe<Scalars['String']['input']>;
  passed: Scalars['Boolean']['input'];
  serializedMetadata?: InputMaybe<Scalars['String']['input']>;
  severity?: InputMaybe<AssetCheckSeverity>;
};

export type ReportAssetCheckEvaluationResult =
  | PythonError
  | ReportAssetCheckEvaluationSuccess
  | UnauthorizedError;

export type ReportAssetCheckEvaluationSuccess = {
  __typename: 'ReportAssetCheckEvaluationSuccess';
  assetKey: AssetKey;
};

export type ReportRunlessAssetEventsParams = {
  assetKey: AssetKeyInput;
  description?: InputMaybe<Scalars['String']['input']>;
  eventType: AssetEventType;
  partitionKeys?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type ReportRunlessAssetEventsResult =
  | PythonError
  | ReportRunlessAssetEventsSuccess
  | UnauthorizedError;

export type ReportRunlessAssetEventsSuccess = {
  __typename: 'ReportRunlessAssetEventsSuccess';
  assetKey: AssetKey;
};

export type RepositoriesOrError = PythonError | RepositoryConnection | RepositoryNotFoundError;

export type Repository = {
  __typename: 'Repository';
  allTopLevelResourceDetails: Array<ResourceDetails>;
  assetGroups: Array<AssetGroup>;
  assetNodes: Array<AssetNode>;
  displayMetadata: Array<RepositoryMetadata>;
  hasLocationDocs: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  jobs: Array<Job>;
  location: RepositoryLocation;
  locationDocsJsonOrError: LocationDocsJsonOrError;
  name: Scalars['String']['output'];
  origin: RepositoryOrigin;
  partitionSets: Array<PartitionSet>;
  pipelines: Array<Pipeline>;
  schedules: Array<Schedule>;
  sensors: Array<Sensor>;
  usedSolid: Maybe<UsedSolid>;
  usedSolids: Array<UsedSolid>;
};

export type RepositorySensorsArgs = {
  sensorType?: InputMaybe<SensorType>;
};

export type RepositoryUsedSolidArgs = {
  name: Scalars['String']['input'];
};

export type RepositoryConnection = {
  __typename: 'RepositoryConnection';
  nodes: Array<Repository>;
};

export type RepositoryLocation = {
  __typename: 'RepositoryLocation';
  dagsterLibraryVersions: Maybe<Array<DagsterLibraryVersion>>;
  environmentPath: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  isReloadSupported: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  repositories: Array<Repository>;
  serverId: Maybe<Scalars['String']['output']>;
};

export {RepositoryLocationLoadStatus};

export type RepositoryLocationNotFound = Error & {
  __typename: 'RepositoryLocationNotFound';
  message: Scalars['String']['output'];
};

export type RepositoryLocationOrLoadError = PythonError | RepositoryLocation;

export type RepositoryMetadata = {
  __typename: 'RepositoryMetadata';
  key: Scalars['String']['output'];
  value: Scalars['String']['output'];
};

export type RepositoryNotFoundError = Error & {
  __typename: 'RepositoryNotFoundError';
  message: Scalars['String']['output'];
  repositoryLocationName: Scalars['String']['output'];
  repositoryName: Scalars['String']['output'];
};

export type RepositoryOrError = PythonError | Repository | RepositoryNotFoundError;

export type RepositoryOrigin = {
  __typename: 'RepositoryOrigin';
  id: Scalars['String']['output'];
  repositoryLocationMetadata: Array<RepositoryMetadata>;
  repositoryLocationName: Scalars['String']['output'];
  repositoryName: Scalars['String']['output'];
};

export type RepositorySelector = {
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
};

export type RequestedMaterializationsForAsset = {
  __typename: 'RequestedMaterializationsForAsset';
  assetKey: AssetKey;
  partitionKeys: Array<Scalars['String']['output']>;
};

export type ResetScheduleMutation = {
  __typename: 'ResetScheduleMutation';
  Output: ScheduleMutationResult;
};

export type ResetSensorMutation = {
  __typename: 'ResetSensorMutation';
  Output: SensorOrError;
};

export type Resource = {
  __typename: 'Resource';
  configField: Maybe<ConfigTypeField>;
  description: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
};

export type ResourceConnection = {
  __typename: 'ResourceConnection';
  resources: Array<Resource>;
};

export type ResourceDetails = {
  __typename: 'ResourceDetails';
  assetKeysUsing: Array<AssetKey>;
  configFields: Array<ConfigTypeField>;
  configuredValues: Array<ConfiguredValue>;
  description: Maybe<Scalars['String']['output']>;
  id: Scalars['String']['output'];
  isTopLevel: Scalars['Boolean']['output'];
  jobsOpsUsing: Array<JobWithOps>;
  name: Scalars['String']['output'];
  nestedResources: Array<NestedResourceEntry>;
  parentResources: Array<NestedResourceEntry>;
  resourceType: Scalars['String']['output'];
  schedulesUsing: Array<Scalars['String']['output']>;
  sensorsUsing: Array<Scalars['String']['output']>;
};

export type ResourceDetailsList = {
  __typename: 'ResourceDetailsList';
  results: Array<ResourceDetails>;
};

export type ResourceDetailsListOrError =
  | PythonError
  | RepositoryNotFoundError
  | ResourceDetailsList;

export type ResourceDetailsOrError = PythonError | ResourceDetails | ResourceNotFoundError;

export type ResourceInitFailureEvent = DisplayableEvent &
  ErrorEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ResourceInitFailureEvent';
    description: Maybe<Scalars['String']['output']>;
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']['output']>;
    markerStart: Maybe<Scalars['String']['output']>;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ResourceInitStartedEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ResourceInitStartedEvent';
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']['output']>;
    markerStart: Maybe<Scalars['String']['output']>;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ResourceInitSuccessEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'ResourceInitSuccessEvent';
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']['output']>;
    markerStart: Maybe<Scalars['String']['output']>;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type ResourceNotFoundError = Error & {
  __typename: 'ResourceNotFoundError';
  message: Scalars['String']['output'];
  resourceName: Scalars['String']['output'];
};

export type ResourceRequirement = {
  __typename: 'ResourceRequirement';
  resourceKey: Scalars['String']['output'];
};

export type ResourceSelector = {
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  resourceName: Scalars['String']['input'];
};

export type ResourcesOrError =
  | InvalidSubsetError
  | PipelineNotFoundError
  | PythonError
  | ResourceConnection;

export type ResumeBackfillResult = PythonError | ResumeBackfillSuccess | UnauthorizedError;

export type ResumeBackfillSuccess = {
  __typename: 'ResumeBackfillSuccess';
  backfillId: Scalars['String']['output'];
};

export type Run = PipelineRun &
  RunsFeedEntry & {
    __typename: 'Run';
    allPools: Maybe<Array<Scalars['String']['output']>>;
    assetCheckSelection: Maybe<Array<AssetCheckhandle>>;
    assetChecks: Maybe<Array<AssetCheckhandle>>;
    assetMaterializations: Array<MaterializationEvent>;
    assetSelection: Maybe<Array<AssetKey>>;
    assets: Array<Asset>;
    canTerminate: Scalars['Boolean']['output'];
    capturedLogs: CapturedLogs;
    creationTime: Scalars['Float']['output'];
    endTime: Maybe<Scalars['Float']['output']>;
    eventConnection: EventConnection;
    executionPlan: Maybe<ExecutionPlan>;
    externalJobSource: Maybe<Scalars['String']['output']>;
    hasConcurrencyKeySlots: Scalars['Boolean']['output'];
    hasDeletePermission: Scalars['Boolean']['output'];
    hasReExecutePermission: Scalars['Boolean']['output'];
    hasRunMetricsEnabled: Scalars['Boolean']['output'];
    hasTerminatePermission: Scalars['Boolean']['output'];
    hasUnconstrainedRootNodes: Scalars['Boolean']['output'];
    id: Scalars['ID']['output'];
    jobName: Scalars['String']['output'];
    mode: Scalars['String']['output'];
    parentPipelineSnapshotId: Maybe<Scalars['String']['output']>;
    parentRunId: Maybe<Scalars['String']['output']>;
    pipeline: PipelineSnapshot | UnknownPipeline;
    pipelineName: Scalars['String']['output'];
    pipelineSnapshotId: Maybe<Scalars['String']['output']>;
    repositoryOrigin: Maybe<RepositoryOrigin>;
    resolvedOpSelection: Maybe<Array<Scalars['String']['output']>>;
    rootConcurrencyKeys: Maybe<Array<Scalars['String']['output']>>;
    rootRunId: Maybe<Scalars['String']['output']>;
    runConfig: Scalars['RunConfigData']['output'];
    runConfigYaml: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    runStatus: RunStatus;
    solidSelection: Maybe<Array<Scalars['String']['output']>>;
    startTime: Maybe<Scalars['Float']['output']>;
    stats: RunStatsSnapshotOrError;
    status: RunStatus;
    stepKeysToExecute: Maybe<Array<Scalars['String']['output']>>;
    stepStats: Array<RunStepStats>;
    tags: Array<PipelineTag>;
    updateTime: Maybe<Scalars['Float']['output']>;
  };

export type RunCapturedLogsArgs = {
  fileKey: Scalars['String']['input'];
};

export type RunEventConnectionArgs = {
  afterCursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type RunCanceledEvent = ErrorEvent &
  MessageEvent &
  RunEvent & {
    __typename: 'RunCanceledEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type RunCancelingEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunCancelingEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type RunConfigSchema = {
  __typename: 'RunConfigSchema';
  allConfigTypes: Array<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
  isRunConfigValid: PipelineConfigValidationResult;
  rootConfigType:
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType;
  rootDefaultYaml: Scalars['String']['output'];
};

export type RunConfigSchemaIsRunConfigValidArgs = {
  runConfigData?: InputMaybe<Scalars['RunConfigData']['input']>;
};

export type RunConfigSchemaOrError =
  | InvalidSubsetError
  | ModeNotFoundError
  | PipelineNotFoundError
  | PythonError
  | RunConfigSchema;

export type RunConfigValidationInvalid = PipelineConfigValidationInvalid & {
  __typename: 'RunConfigValidationInvalid';
  errors: Array<
    | FieldNotDefinedConfigError
    | FieldsNotDefinedConfigError
    | MissingFieldConfigError
    | MissingFieldsConfigError
    | RuntimeMismatchConfigError
    | SelectorTypeConfigError
  >;
  pipelineName: Scalars['String']['output'];
};

export type RunConflict = Error &
  PipelineRunConflict & {
    __typename: 'RunConflict';
    message: Scalars['String']['output'];
  };

export type RunDequeuedEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunDequeuedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type RunEnqueuedEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunEnqueuedEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type RunEvent = {
  pipelineName: Scalars['String']['output'];
};

export type RunFailureEvent = ErrorEvent &
  MessageEvent &
  RunEvent & {
    __typename: 'RunFailureEvent';
    error: Maybe<PythonError>;
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type RunGroup = {
  __typename: 'RunGroup';
  rootRunId: Scalars['String']['output'];
  runs: Maybe<Array<Maybe<Run>>>;
};

export type RunGroupNotFoundError = Error & {
  __typename: 'RunGroupNotFoundError';
  message: Scalars['String']['output'];
  runId: Scalars['String']['output'];
};

export type RunGroupOrError = PythonError | RunGroup | RunGroupNotFoundError;

export type RunGroups = {
  __typename: 'RunGroups';
  results: Array<RunGroup>;
};

export type RunIds = {
  __typename: 'RunIds';
  results: Array<Scalars['String']['output']>;
};

export type RunIdsOrError = InvalidPipelineRunsFilterError | PythonError | RunIds;

export type RunLauncher = {
  __typename: 'RunLauncher';
  name: Scalars['String']['output'];
};

export type RunMarker = {
  __typename: 'RunMarker';
  endTime: Maybe<Scalars['Float']['output']>;
  startTime: Maybe<Scalars['Float']['output']>;
};

export type RunNotFoundError = Error &
  PipelineRunNotFoundError & {
    __typename: 'RunNotFoundError';
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
  };

export type RunOrError = PythonError | Run | RunNotFoundError;

export type RunQueueConfig = {
  __typename: 'RunQueueConfig';
  isOpConcurrencyAware: Maybe<Scalars['Boolean']['output']>;
  maxConcurrentRuns: Scalars['Int']['output'];
  tagConcurrencyLimitsYaml: Maybe<Scalars['String']['output']>;
};

export type RunRequest = {
  __typename: 'RunRequest';
  assetChecks: Maybe<Array<AssetCheckhandle>>;
  assetSelection: Maybe<Array<AssetKey>>;
  jobName: Maybe<Scalars['String']['output']>;
  runConfigYaml: Scalars['String']['output'];
  runKey: Maybe<Scalars['String']['output']>;
  tags: Array<PipelineTag>;
};

export type RunStartEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunStartEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type RunStartingEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunStartingEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type RunStatsSnapshot = PipelineRunStatsSnapshot & {
  __typename: 'RunStatsSnapshot';
  endTime: Maybe<Scalars['Float']['output']>;
  enqueuedTime: Maybe<Scalars['Float']['output']>;
  expectations: Scalars['Int']['output'];
  id: Scalars['String']['output'];
  launchTime: Maybe<Scalars['Float']['output']>;
  materializations: Scalars['Int']['output'];
  runId: Scalars['String']['output'];
  startTime: Maybe<Scalars['Float']['output']>;
  stepsFailed: Scalars['Int']['output'];
  stepsSucceeded: Scalars['Int']['output'];
};

export type RunStatsSnapshotOrError = PythonError | RunStatsSnapshot;

export {RunStatus};

export type RunStepStats = PipelineRunStepStats & {
  __typename: 'RunStepStats';
  attempts: Array<RunMarker>;
  endTime: Maybe<Scalars['Float']['output']>;
  expectationResults: Array<ExpectationResult>;
  markers: Array<RunMarker>;
  materializations: Array<MaterializationEvent>;
  runId: Scalars['String']['output'];
  startTime: Maybe<Scalars['Float']['output']>;
  status: Maybe<StepEventStatus>;
  stepKey: Scalars['String']['output'];
};

export type RunSuccessEvent = MessageEvent &
  RunEvent & {
    __typename: 'RunSuccessEvent';
    eventType: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars['String']['output'];
    pipelineName: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type RunTagKeys = {
  __typename: 'RunTagKeys';
  keys: Array<Scalars['String']['output']>;
};

export type RunTagKeysOrError = PythonError | RunTagKeys;

export type RunTags = {
  __typename: 'RunTags';
  tags: Array<PipelineTagAndValues>;
};

export type RunTagsOrError = PythonError | RunTags;

export type Runs = PipelineRuns & {
  __typename: 'Runs';
  count: Maybe<Scalars['Int']['output']>;
  results: Array<Run>;
};

export type RunsFeedConnection = {
  __typename: 'RunsFeedConnection';
  cursor: Scalars['String']['output'];
  hasMore: Scalars['Boolean']['output'];
  results: Array<PartitionBackfill | Run>;
};

export type RunsFeedConnectionOrError = PythonError | RunsFeedConnection;

export type RunsFeedCount = {
  __typename: 'RunsFeedCount';
  count: Scalars['Int']['output'];
};

export type RunsFeedCountOrError = PythonError | RunsFeedCount;

export type RunsFeedEntry = {
  assetCheckSelection: Maybe<Array<AssetCheckhandle>>;
  assetSelection: Maybe<Array<AssetKey>>;
  creationTime: Scalars['Float']['output'];
  endTime: Maybe<Scalars['Float']['output']>;
  id: Scalars['ID']['output'];
  jobName: Maybe<Scalars['String']['output']>;
  runStatus: Maybe<RunStatus>;
  startTime: Maybe<Scalars['Float']['output']>;
  tags: Array<PipelineTag>;
};

export {RunsFeedView};

export type RunsFilter = {
  createdAfter?: InputMaybe<Scalars['Float']['input']>;
  createdBefore?: InputMaybe<Scalars['Float']['input']>;
  mode?: InputMaybe<Scalars['String']['input']>;
  pipelineName?: InputMaybe<Scalars['String']['input']>;
  runIds?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  snapshotId?: InputMaybe<Scalars['String']['input']>;
  statuses?: InputMaybe<Array<RunStatus>>;
  tags?: InputMaybe<Array<ExecutionTag>>;
  updatedAfter?: InputMaybe<Scalars['Float']['input']>;
  updatedBefore?: InputMaybe<Scalars['Float']['input']>;
};

export type RunsOrError = InvalidPipelineRunsFilterError | PythonError | Runs;

export type RuntimeMismatchConfigError = PipelineConfigValidationError & {
  __typename: 'RuntimeMismatchConfigError';
  message: Scalars['String']['output'];
  path: Array<Scalars['String']['output']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
  valueRep: Maybe<Scalars['String']['output']>;
};

export type ScalarUnionConfigType = ConfigType & {
  __typename: 'ScalarUnionConfigType';
  description: Maybe<Scalars['String']['output']>;
  isSelector: Scalars['Boolean']['output'];
  key: Scalars['String']['output'];
  nonScalarType:
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType;
  nonScalarTypeKey: Scalars['String']['output'];
  recursiveConfigTypes: Array<
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType
  >;
  scalarType:
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType;
  scalarTypeKey: Scalars['String']['output'];
  typeParamKeys: Array<Scalars['String']['output']>;
};

export type Schedule = {
  __typename: 'Schedule';
  assetSelection: Maybe<AssetSelection>;
  canReset: Scalars['Boolean']['output'];
  cronSchedule: Scalars['String']['output'];
  defaultStatus: InstigationStatus;
  description: Maybe<Scalars['String']['output']>;
  executionTimezone: Maybe<Scalars['String']['output']>;
  futureTick: DryRunInstigationTick;
  futureTicks: DryRunInstigationTicks;
  id: Scalars['ID']['output'];
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  mode: Scalars['String']['output'];
  name: Scalars['String']['output'];
  owners: Array<DefinitionOwner>;
  partitionSet: Maybe<PartitionSet>;
  pipelineName: Scalars['String']['output'];
  potentialTickTimestamps: Array<Scalars['Float']['output']>;
  scheduleState: InstigationState;
  solidSelection: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  tags: Array<DefinitionTag>;
};

export type ScheduleFutureTickArgs = {
  tickTimestamp: Scalars['Int']['input'];
};

export type ScheduleFutureTicksArgs = {
  cursor?: InputMaybe<Scalars['Float']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  until?: InputMaybe<Scalars['Float']['input']>;
};

export type SchedulePotentialTickTimestampsArgs = {
  lowerLimit?: InputMaybe<Scalars['Int']['input']>;
  startTimestamp?: InputMaybe<Scalars['Float']['input']>;
  upperLimit?: InputMaybe<Scalars['Int']['input']>;
};

export type ScheduleData = {
  __typename: 'ScheduleData';
  cronSchedule: Scalars['String']['output'];
  startTimestamp: Maybe<Scalars['Float']['output']>;
};

export type ScheduleDryRunResult = DryRunInstigationTick | PythonError | ScheduleNotFoundError;

export type ScheduleMutationResult =
  | PythonError
  | ScheduleNotFoundError
  | ScheduleStateResult
  | UnauthorizedError;

export type ScheduleNotFoundError = Error & {
  __typename: 'ScheduleNotFoundError';
  message: Scalars['String']['output'];
  scheduleName: Scalars['String']['output'];
};

export type ScheduleOrError = PythonError | Schedule | ScheduleNotFoundError;

export type ScheduleSelector = {
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  scheduleName: Scalars['String']['input'];
};

export type ScheduleStateResult = {
  __typename: 'ScheduleStateResult';
  scheduleState: InstigationState;
};

export {ScheduleStatus};

export type ScheduleTick = {
  __typename: 'ScheduleTick';
  status: InstigationTickStatus;
  tickId: Scalars['String']['output'];
  tickSpecificData: Maybe<ScheduleTickSpecificData>;
  timestamp: Scalars['Float']['output'];
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
  schedulerClass: Maybe<Scalars['String']['output']>;
};

export type SchedulerNotDefinedError = Error & {
  __typename: 'SchedulerNotDefinedError';
  message: Scalars['String']['output'];
};

export type SchedulerOrError = PythonError | Scheduler | SchedulerNotDefinedError;

export type Schedules = {
  __typename: 'Schedules';
  results: Array<Schedule>;
};

export type SchedulesOrError = PythonError | RepositoryNotFoundError | Schedules;

export type SelectorTypeConfigError = PipelineConfigValidationError & {
  __typename: 'SelectorTypeConfigError';
  incomingFields: Array<Scalars['String']['output']>;
  message: Scalars['String']['output'];
  path: Array<Scalars['String']['output']>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type Sensor = {
  __typename: 'Sensor';
  assetSelection: Maybe<AssetSelection>;
  canReset: Scalars['Boolean']['output'];
  defaultStatus: InstigationStatus;
  description: Maybe<Scalars['String']['output']>;
  hasCursorUpdatePermissions: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  jobOriginId: Scalars['String']['output'];
  metadata: SensorMetadata;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  minIntervalSeconds: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  nextTick: Maybe<DryRunInstigationTick>;
  owners: Array<DefinitionOwner>;
  sensorState: InstigationState;
  sensorType: SensorType;
  tags: Array<DefinitionTag>;
  targets: Maybe<Array<Target>>;
};

export type SensorData = {
  __typename: 'SensorData';
  lastCursor: Maybe<Scalars['String']['output']>;
  lastRunKey: Maybe<Scalars['String']['output']>;
  lastTickTimestamp: Maybe<Scalars['Float']['output']>;
};

export type SensorDryRunResult = DryRunInstigationTick | PythonError | SensorNotFoundError;

export type SensorMetadata = {
  __typename: 'SensorMetadata';
  assetKeys: Maybe<Array<AssetKey>>;
};

export type SensorNotFoundError = Error & {
  __typename: 'SensorNotFoundError';
  message: Scalars['String']['output'];
  sensorName: Scalars['String']['output'];
};

export type SensorOrError = PythonError | Sensor | SensorNotFoundError | UnauthorizedError;

export type SensorSelector = {
  repositoryLocationName: Scalars['String']['input'];
  repositoryName: Scalars['String']['input'];
  sensorName: Scalars['String']['input'];
};

export {SensorType};

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
  repositoryLocationName: Scalars['String']['output'];
};

export type SinceConditionMetadata = {
  __typename: 'SinceConditionMetadata';
  resetEvaluationId: Maybe<Scalars['ID']['output']>;
  resetTimestamp: Maybe<Scalars['Float']['output']>;
  triggerEvaluationId: Maybe<Scalars['ID']['output']>;
  triggerTimestamp: Maybe<Scalars['Float']['output']>;
};

export type Solid = {
  __typename: 'Solid';
  definition: CompositeSolidDefinition | SolidDefinition;
  inputs: Array<Input>;
  isDynamicMapped: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  outputs: Array<Output>;
};

export type SolidContainer = {
  description: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  modes: Array<Mode>;
  name: Scalars['String']['output'];
  solidHandle: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
};

export type SolidContainerSolidHandleArgs = {
  handleID: Scalars['String']['input'];
};

export type SolidContainerSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars['String']['input']>;
};

export type SolidDefinition = ISolidDefinition & {
  __typename: 'SolidDefinition';
  assetNodes: Array<AssetNode>;
  configField: Maybe<ConfigTypeField>;
  description: Maybe<Scalars['String']['output']>;
  inputDefinitions: Array<InputDefinition>;
  metadata: Array<MetadataItemDefinition>;
  name: Scalars['String']['output'];
  outputDefinitions: Array<OutputDefinition>;
  pool: Maybe<Scalars['String']['output']>;
  pools: Array<Scalars['String']['output']>;
  requiredResources: Array<ResourceRequirement>;
};

export type SolidHandle = {
  __typename: 'SolidHandle';
  handleID: Scalars['String']['output'];
  parent: Maybe<SolidHandle>;
  solid: Solid;
  stepStats: Maybe<SolidStepStatsOrError>;
};

export type SolidHandleStepStatsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};

export type SolidStepStatsConnection = {
  __typename: 'SolidStepStatsConnection';
  nodes: Array<RunStepStats>;
};

export type SolidStepStatsOrError = SolidStepStatsConnection | SolidStepStatusUnavailableError;

export type SolidStepStatusUnavailableError = Error & {
  __typename: 'SolidStepStatusUnavailableError';
  message: Scalars['String']['output'];
};

export type SourceLocation = LocalFileCodeReference | UrlCodeReference;

export type SpecificPartitionAssetConditionEvaluationNode = {
  __typename: 'SpecificPartitionAssetConditionEvaluationNode';
  childUniqueIds: Array<Scalars['String']['output']>;
  description: Scalars['String']['output'];
  entityKey: EntityKey;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  status: AssetConditionEvaluationStatus;
  uniqueId: Scalars['String']['output'];
};

export type StaleCause = {
  __typename: 'StaleCause';
  category: StaleCauseCategory;
  dependency: Maybe<AssetKey>;
  dependencyPartitionKey: Maybe<Scalars['String']['output']>;
  key: AssetKey;
  partitionKey: Maybe<Scalars['String']['output']>;
  reason: Scalars['String']['output'];
};

export {StaleCauseCategory};

export {StaleStatus};

export type StartScheduleMutation = {
  __typename: 'StartScheduleMutation';
  Output: ScheduleMutationResult;
};

export type StepEvent = {
  solidHandleID: Maybe<Scalars['String']['output']>;
  stepKey: Maybe<Scalars['String']['output']>;
};

export {StepEventStatus};

export type StepExecution = {
  marshalledInputs?: InputMaybe<Array<MarshalledInput>>;
  marshalledOutputs?: InputMaybe<Array<MarshalledOutput>>;
  stepKey: Scalars['String']['input'];
};

export type StepExpectationResultEvent = MessageEvent &
  StepEvent & {
    __typename: 'StepExpectationResultEvent';
    eventType: Maybe<DagsterEventType>;
    expectationResult: ExpectationResult;
    level: LogLevel;
    message: Scalars['String']['output'];
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export {StepKind};

export type StepOutputHandle = {
  outputName: Scalars['String']['input'];
  stepKey: Scalars['String']['input'];
};

export type StepWorkerStartedEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'StepWorkerStartedEvent';
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']['output']>;
    markerStart: Maybe<Scalars['String']['output']>;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
  };

export type StepWorkerStartingEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename: 'StepWorkerStartingEvent';
    description: Maybe<Scalars['String']['output']>;
    eventType: Maybe<DagsterEventType>;
    label: Maybe<Scalars['String']['output']>;
    level: LogLevel;
    markerEnd: Maybe<Scalars['String']['output']>;
    markerStart: Maybe<Scalars['String']['output']>;
    message: Scalars['String']['output'];
    metadataEntries: Array<
      | AssetMetadataEntry
      | BoolMetadataEntry
      | CodeReferencesMetadataEntry
      | FloatMetadataEntry
      | IntMetadataEntry
      | JobMetadataEntry
      | JsonMetadataEntry
      | MarkdownMetadataEntry
      | NotebookMetadataEntry
      | NullMetadataEntry
      | PathMetadataEntry
      | PipelineRunMetadataEntry
      | PoolMetadataEntry
      | PythonArtifactMetadataEntry
      | TableColumnLineageMetadataEntry
      | TableMetadataEntry
      | TableSchemaMetadataEntry
      | TextMetadataEntry
      | TimestampMetadataEntry
      | UrlMetadataEntry
    >;
    runId: Scalars['String']['output'];
    solidHandleID: Maybe<Scalars['String']['output']>;
    stepKey: Maybe<Scalars['String']['output']>;
    timestamp: Scalars['String']['output'];
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

export type Subscription = {
  __typename: 'Subscription';
  capturedLogs: CapturedLogs;
  locationStateChangeEvents: LocationStateChangeSubscription;
  pipelineRunLogs: PipelineRunLogsSubscriptionPayload;
};

export type SubscriptionCapturedLogsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  logKey: Array<Scalars['String']['input']>;
};

export type SubscriptionPipelineRunLogsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  runId: Scalars['ID']['input'];
};

export type Table = {
  __typename: 'Table';
  records: Array<Scalars['String']['output']>;
  schema: TableSchema;
};

export type TableColumn = {
  __typename: 'TableColumn';
  constraints: TableColumnConstraints;
  description: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  tags: Array<DefinitionTag>;
  type: Scalars['String']['output'];
};

export type TableColumnConstraints = {
  __typename: 'TableColumnConstraints';
  nullable: Scalars['Boolean']['output'];
  other: Array<Scalars['String']['output']>;
  unique: Scalars['Boolean']['output'];
};

export type TableColumnDep = {
  __typename: 'TableColumnDep';
  assetKey: AssetKey;
  columnName: Scalars['String']['output'];
};

export type TableColumnLineageEntry = {
  __typename: 'TableColumnLineageEntry';
  columnDeps: Array<TableColumnDep>;
  columnName: Scalars['String']['output'];
};

export type TableColumnLineageMetadataEntry = MetadataEntry & {
  __typename: 'TableColumnLineageMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  lineage: Array<TableColumnLineageEntry>;
};

export type TableConstraints = {
  __typename: 'TableConstraints';
  other: Array<Scalars['String']['output']>;
};

export type TableMetadataEntry = MetadataEntry & {
  __typename: 'TableMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  table: Table;
};

export type TableSchema = {
  __typename: 'TableSchema';
  columns: Array<TableColumn>;
  constraints: Maybe<TableConstraints>;
};

export type TableSchemaMetadataEntry = MetadataEntry & {
  __typename: 'TableSchemaMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  schema: TableSchema;
};

export type TagInput = {
  key: Scalars['String']['input'];
  value: Scalars['String']['input'];
};

export type Target = {
  __typename: 'Target';
  mode: Scalars['String']['output'];
  pipelineName: Scalars['String']['output'];
  solidSelection: Maybe<Array<Scalars['String']['output']>>;
};

export type TeamAssetOwner = {
  __typename: 'TeamAssetOwner';
  team: Scalars['String']['output'];
};

export type TeamDefinitionOwner = {
  __typename: 'TeamDefinitionOwner';
  team: Scalars['String']['output'];
};

export type TerminatePipelineExecutionFailure = {
  message: Scalars['String']['output'];
  run: Run;
};

export type TerminatePipelineExecutionSuccess = {
  run: Run;
};

export type TerminateRunFailure = TerminatePipelineExecutionFailure & {
  __typename: 'TerminateRunFailure';
  message: Scalars['String']['output'];
  run: Run;
};

export type TerminateRunMutation = {
  __typename: 'TerminateRunMutation';
  Output: TerminateRunResult;
};

export {TerminateRunPolicy};

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

export type TerminateRunsResult = {
  __typename: 'TerminateRunsResult';
  terminateRunResults: Array<TerminateRunResult>;
};

export type TerminateRunsResultOrError = PythonError | TerminateRunsResult;

export type TestFields = {
  __typename: 'TestFields';
  alwaysException: Maybe<Scalars['String']['output']>;
  asyncString: Maybe<Scalars['String']['output']>;
};

export type TextMetadataEntry = MetadataEntry & {
  __typename: 'TextMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  text: Scalars['String']['output'];
};

export type TextRuleEvaluationData = {
  __typename: 'TextRuleEvaluationData';
  text: Maybe<Scalars['String']['output']>;
};

export type TickEvaluation = {
  __typename: 'TickEvaluation';
  cursor: Maybe<Scalars['String']['output']>;
  dynamicPartitionsRequests: Maybe<Array<DynamicPartitionRequest>>;
  error: Maybe<PythonError>;
  runRequests: Maybe<Array<RunRequest>>;
  skipReason: Maybe<Scalars['String']['output']>;
};

export type TimePartitionRangeStatus = {
  __typename: 'TimePartitionRangeStatus';
  endKey: Scalars['String']['output'];
  endTime: Scalars['Float']['output'];
  startKey: Scalars['String']['output'];
  startTime: Scalars['Float']['output'];
  status: PartitionRangeStatus;
};

export type TimePartitionStatuses = {
  __typename: 'TimePartitionStatuses';
  ranges: Array<TimePartitionRangeStatus>;
};

export type TimeWindowFreshnessPolicy = {
  __typename: 'TimeWindowFreshnessPolicy';
  failWindowSeconds: Scalars['Int']['output'];
  warnWindowSeconds: Maybe<Scalars['Int']['output']>;
};

export type TimestampMetadataEntry = MetadataEntry & {
  __typename: 'TimestampMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  timestamp: Scalars['Float']['output'];
};

export type TypeCheck = DisplayableEvent & {
  __typename: 'TypeCheck';
  description: Maybe<Scalars['String']['output']>;
  label: Maybe<Scalars['String']['output']>;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  success: Scalars['Boolean']['output'];
};

export type UnauthorizedError = Error & {
  __typename: 'UnauthorizedError';
  message: Scalars['String']['output'];
};

export type UnknownPipeline = PipelineReference & {
  __typename: 'UnknownPipeline';
  name: Scalars['String']['output'];
  solidSelection: Maybe<Array<Scalars['String']['output']>>;
};

export type UnpartitionedAssetConditionEvaluationNode = {
  __typename: 'UnpartitionedAssetConditionEvaluationNode';
  childUniqueIds: Array<Scalars['String']['output']>;
  description: Scalars['String']['output'];
  endTimestamp: Maybe<Scalars['Float']['output']>;
  entityKey: EntityKey;
  metadataEntries: Array<
    | AssetMetadataEntry
    | BoolMetadataEntry
    | CodeReferencesMetadataEntry
    | FloatMetadataEntry
    | IntMetadataEntry
    | JobMetadataEntry
    | JsonMetadataEntry
    | MarkdownMetadataEntry
    | NotebookMetadataEntry
    | NullMetadataEntry
    | PathMetadataEntry
    | PipelineRunMetadataEntry
    | PoolMetadataEntry
    | PythonArtifactMetadataEntry
    | TableColumnLineageMetadataEntry
    | TableMetadataEntry
    | TableSchemaMetadataEntry
    | TextMetadataEntry
    | TimestampMetadataEntry
    | UrlMetadataEntry
  >;
  startTimestamp: Maybe<Scalars['Float']['output']>;
  status: AssetConditionEvaluationStatus;
  uniqueId: Scalars['String']['output'];
};

export type UnpartitionedAssetStatus = {
  __typename: 'UnpartitionedAssetStatus';
  assetKey: AssetKey;
  failed: Scalars['Boolean']['output'];
  inProgress: Scalars['Boolean']['output'];
  materialized: Scalars['Boolean']['output'];
};

export type UnsupportedOperationError = Error & {
  __typename: 'UnsupportedOperationError';
  message: Scalars['String']['output'];
};

export type UrlCodeReference = {
  __typename: 'UrlCodeReference';
  label: Maybe<Scalars['String']['output']>;
  url: Scalars['String']['output'];
};

export type UrlMetadataEntry = MetadataEntry & {
  __typename: 'UrlMetadataEntry';
  description: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  url: Scalars['String']['output'];
};

export type UsedSolid = {
  __typename: 'UsedSolid';
  definition: CompositeSolidDefinition | SolidDefinition;
  invocations: Array<NodeInvocationSite>;
};

export type UserAssetOwner = {
  __typename: 'UserAssetOwner';
  email: Scalars['String']['output'];
};

export type UserDefinitionOwner = {
  __typename: 'UserDefinitionOwner';
  email: Scalars['String']['output'];
};

export type WaitingOnKeysRuleEvaluationData = {
  __typename: 'WaitingOnKeysRuleEvaluationData';
  waitingOnAssetKeys: Maybe<Array<AssetKey>>;
};

export type Workspace = {
  __typename: 'Workspace';
  id: Scalars['String']['output'];
  locationEntries: Array<WorkspaceLocationEntry>;
};

export type WorkspaceLocationEntry = {
  __typename: 'WorkspaceLocationEntry';
  definitionsSource: DefinitionsSource;
  defsStateInfo: Maybe<DefsStateInfo>;
  displayMetadata: Array<RepositoryMetadata>;
  featureFlags: Array<FeatureFlag>;
  id: Scalars['ID']['output'];
  loadStatus: RepositoryLocationLoadStatus;
  locationOrLoadError: Maybe<RepositoryLocationOrLoadError>;
  name: Scalars['String']['output'];
  permissions: Array<Permission>;
  updatedTimestamp: Scalars['Float']['output'];
  versionKey: Scalars['String']['output'];
};

export type WorkspaceLocationEntryOrError = PythonError | WorkspaceLocationEntry;

export type WorkspaceLocationStatusEntries = {
  __typename: 'WorkspaceLocationStatusEntries';
  entries: Array<WorkspaceLocationStatusEntry>;
};

export type WorkspaceLocationStatusEntriesOrError = PythonError | WorkspaceLocationStatusEntries;

export type WorkspaceLocationStatusEntry = {
  __typename: 'WorkspaceLocationStatusEntry';
  id: Scalars['ID']['output'];
  loadStatus: RepositoryLocationLoadStatus;
  name: Scalars['String']['output'];
  permissions: Array<Permission>;
  updateTimestamp: Scalars['Float']['output'];
  versionKey: Scalars['String']['output'];
};

export type WorkspaceOrError = PythonError | Workspace;

export type WrappingConfigType = {
  ofType:
    | ArrayConfigType
    | CompositeConfigType
    | EnumConfigType
    | MapConfigType
    | NullableConfigType
    | RegularConfigType
    | ScalarUnionConfigType;
};

export type WrappingDagsterType = {
  ofType: ListDagsterType | NullableDagsterType | RegularDagsterType;
};
