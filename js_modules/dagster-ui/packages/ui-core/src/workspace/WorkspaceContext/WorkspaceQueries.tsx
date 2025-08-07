import {gql} from '../../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {ASSET_TABLE_DEFINITION_FRAGMENT} from '../../assets/AssetTableFragment';
import {BASIC_INSTIGATION_STATE_FRAGMENT} from '../../overview/BasicInstigationStateFragment';
import {RESOURCE_ENTRY_FRAGMENT} from '../../resources/WorkspaceResourcesQuery';
import {SENSOR_SWITCH_FRAGMENT} from '../../sensors/SensorSwitchFragment';
import {REPOSITORY_INFO_FRAGMENT} from '../RepositoryInformation';

export const WORKSPACE_DISPLAY_METADATA_FRAGMENT = gql`
  fragment WorkspaceDisplayMetadata on RepositoryMetadata {
    key
    value
  }
`;

export const WORKSPACE_PIPELINE_FRAGMENT = gql`
  fragment WorkspacePipeline on Pipeline {
    id
    name
    isJob
    isAssetJob
    externalJobSource
    pipelineSnapshotId
  }
`;

export const WORKSPACE_SCHEDULE_FRAGMENT = gql`
  fragment WorkspaceSchedule on Schedule {
    id
    cronSchedule
    executionTimezone
    mode
    name
    pipelineName
    scheduleState {
      id
      status
      ...BasicInstigationStateFragment
    }
    tags {
      key
      value
    }
  }
  ${BASIC_INSTIGATION_STATE_FRAGMENT}
`;

export const WORKSPACE_PARTITION_SET_FRAGMENT = gql`
  fragment WorkspacePartitionSet on PartitionSet {
    id
    name
    pipelineName
  }
`;

export const WORKSPACE_SENSOR_FRAGMENT = gql`
  fragment WorkspaceSensor on Sensor {
    id
    name
    tags {
      key
      value
    }
    targets {
      mode
      pipelineName
    }
    sensorState {
      id
      status
      ...BasicInstigationStateFragment
    }
    sensorType
    ...SensorSwitchFragment
  }
  ${BASIC_INSTIGATION_STATE_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
`;

export const PARTIAL_WORKSPACE_REPOSITORY_FRAGMENT = gql`
  fragment PartialWorkspaceRepository on Repository {
    id
    name
    pipelines {
      id
      ...WorkspacePipeline
    }
    schedules {
      id
      ...WorkspaceSchedule
    }
    sensors {
      id
      ...WorkspaceSensor
    }
    partitionSets {
      ...WorkspacePartitionSet
    }
    allTopLevelResourceDetails {
      id
      ...ResourceEntryFragment
    }
    ...RepositoryInfoFragment
  }
  ${WORKSPACE_PIPELINE_FRAGMENT}
  ${WORKSPACE_SCHEDULE_FRAGMENT}
  ${WORKSPACE_SENSOR_FRAGMENT}
  ${WORKSPACE_PARTITION_SET_FRAGMENT}
  ${REPOSITORY_INFO_FRAGMENT}
  ${RESOURCE_ENTRY_FRAGMENT}
`;

export const PARTIAL_WORKSPACE_LOCATION_FRAGMENT = gql`
  fragment PartialWorkspaceLocation on RepositoryLocation {
    id
    isReloadSupported
    serverId
    name
    dagsterLibraryVersions {
      name
      version
    }
    repositories {
      id
      ...PartialWorkspaceRepository
    }
  }
  ${PARTIAL_WORKSPACE_REPOSITORY_FRAGMENT}
`;

export const PARTIAL_WORKSPACE_LOCATION_NODE_FRAGMENT = gql`
  fragment PartialWorkspaceLocationNode on WorkspaceLocationEntry {
    id
    name
    loadStatus
    displayMetadata {
      ...WorkspaceDisplayMetadata
    }
    updatedTimestamp
    versionKey
    featureFlags {
      name
      enabled
    }
    stateVersions {
      versionInfo {
        name
        version
        createTimestamp
      }
    }
    locationOrLoadError {
      ... on RepositoryLocation {
        id
        ...PartialWorkspaceLocation
      }
      ...PythonErrorFragment
    }
  }
  ${WORKSPACE_DISPLAY_METADATA_FRAGMENT}
  ${PARTIAL_WORKSPACE_LOCATION_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const LOCATION_STATUS_ENTRY_FRAGMENT = gql`
  fragment LocationStatusEntryFragment on WorkspaceLocationStatusEntry {
    id
    name
    loadStatus
    updateTimestamp
    versionKey
  }
`;

export const WORKSPACE_ASSET_FRAGMENT = gql`
  fragment WorkspaceAsset on AssetNode {
    id
    ...AssetTableDefinitionFragment
    graphName
    opVersion
    dependencyKeys {
      path
    }
    dependedByKeys {
      path
    }
  }
  ${ASSET_TABLE_DEFINITION_FRAGMENT}
`;

export const WORKSPACE_REPOSITORY_ASSETS_FRAGMENT = gql`
  fragment WorkspaceRepositoryAssets on Repository {
    id
    name
    assetNodes {
      id
      ...WorkspaceAsset
    }
    assetGroups {
      ...WorkspaceAssetGroup
    }
  }
  ${WORKSPACE_ASSET_FRAGMENT}
  fragment WorkspaceAssetGroup on AssetGroup {
    id
    groupName
  }
`;

export const WORKSPACE_LOCATION_ASSETS_FRAGMENT = gql`
  fragment WorkspaceLocationAssets on RepositoryLocation {
    id
    name
    repositories {
      id
      ...WorkspaceRepositoryAssets
    }
  }
  ${WORKSPACE_REPOSITORY_ASSETS_FRAGMENT}
`;

export const WORKSPACE_LOCATION_FRAGMENT = gql`
  fragment WorkspaceLocation on RepositoryLocation {
    ...PartialWorkspaceLocation
    ...WorkspaceLocationAssets
  }
  ${PARTIAL_WORKSPACE_LOCATION_FRAGMENT}
  ${WORKSPACE_LOCATION_ASSETS_FRAGMENT}
`;

export const WORKSPACE_LOCATION_ASSETS_ENTRY_FRAGMENT = gql`
  fragment WorkspaceLocationAssetsEntry on WorkspaceLocationEntry {
    id
    name
    loadStatus
    updatedTimestamp
    versionKey
    locationOrLoadError {
      ... on RepositoryLocation {
        id
        ...WorkspaceLocationAssets
      }
      ...PythonErrorFragment
    }
  }
  ${WORKSPACE_LOCATION_ASSETS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

// Queries
export const LOCATION_WORKSPACE_QUERY = gql`
  query LocationWorkspaceQuery($name: String!) {
    workspaceLocationEntryOrError(name: $name) {
      ...PartialWorkspaceLocationNode
      ...PythonErrorFragment
    }
  }
  ${PARTIAL_WORKSPACE_LOCATION_NODE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const WORKSPACE_LATEST_STATE_VERSIONS_QUERY = gql`
  query WorkspaceLatestStateVersionsQuery {
    workspaceOrError {
      ... on Workspace {
        id
        latestStateVersions {
          versionInfo {
            name
            version
            createTimestamp
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

export const CODE_LOCATION_STATUS_QUERY = gql`
  query CodeLocationStatusQuery {
    locationStatusesOrError {
      ... on WorkspaceLocationStatusEntries {
        entries {
          id
          ...LocationStatusEntryFragment
        }
      }
    }
  }
  ${LOCATION_STATUS_ENTRY_FRAGMENT}
`;

export const LOCATION_WORKSPACE_ASSETS_QUERY = gql`
  query LocationWorkspaceAssetsQuery($name: String!) {
    workspaceLocationEntryOrError(name: $name) {
      ...WorkspaceLocationAssetsEntry
      ...PythonErrorFragment
    }
  }
  ${WORKSPACE_LOCATION_ASSETS_ENTRY_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

/*
 * This fragment isn't used to make a query, but the type is used when merging
 * PartialWorkspaceRepository and WorkspaceRepositoryAssets together
 */
export const WORKSPACE_LOCATION_NODE_FRAGMENT = gql`
  fragment WorkspaceLocationNode on WorkspaceLocationEntry {
    id
    name
    loadStatus
    displayMetadata {
      ...WorkspaceDisplayMetadata
    }
    updatedTimestamp
    versionKey
    featureFlags {
      name
      enabled
    }
    stateVersions {
      versionInfo {
        name
        version
        createTimestamp
      }
    }
    locationOrLoadError {
      ...WorkspaceRepositoryLocation
      ...PythonErrorFragment
    }
  }
  fragment WorkspaceRepositoryLocation on RepositoryLocation {
    id
    ...WorkspaceLocation
    ...WorkspaceLocationAssets
  }
  ${WORKSPACE_DISPLAY_METADATA_FRAGMENT}
  ${WORKSPACE_LOCATION_FRAGMENT}
  ${WORKSPACE_LOCATION_ASSETS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const WORKSPACE_REPOSITORY_FRAGMENT = gql`
  fragment WorkspaceRepository on Repository {
    ...PartialWorkspaceRepository
    ...WorkspaceRepositoryAssets
  }
  ${PARTIAL_WORKSPACE_REPOSITORY_FRAGMENT}
  ${WORKSPACE_REPOSITORY_ASSETS_FRAGMENT}
`;
