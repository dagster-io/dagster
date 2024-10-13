import {gql} from '../../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {BASIC_INSTIGATION_STATE_FRAGMENT} from '../../overview/BasicInstigationStateFragment';
import {RESOURCE_ENTRY_FRAGMENT} from '../../resources/WorkspaceResourcesRoot';
import {SENSOR_SWITCH_FRAGMENT} from '../../sensors/SensorSwitch';
import {REPOSITORY_INFO_FRAGMENT} from '../RepositoryInformation';

export const LOCATION_WORKSPACE_QUERY = gql`
  query LocationWorkspaceQuery($name: String!) {
    workspaceLocationEntryOrError(name: $name) {
      ...WorkspaceLocationNode
      ...PythonErrorFragment
    }
  }

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
    locationOrLoadError {
      ... on RepositoryLocation {
        id
        ...WorkspaceLocation
      }
      ...PythonErrorFragment
    }
  }

  fragment WorkspaceDisplayMetadata on RepositoryMetadata {
    key
    value
  }

  fragment WorkspaceLocation on RepositoryLocation {
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
      ...WorkspaceRepository
    }
  }

  fragment WorkspaceRepository on Repository {
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
      id
      mode
      pipelineName
    }
    assetGroups {
      id
      groupName
    }
    allTopLevelResourceDetails {
      id
      ...ResourceEntryFragment
    }
    ...RepositoryInfoFragment
  }

  fragment WorkspacePipeline on Pipeline {
    id
    name
    isJob
    isAssetJob
    pipelineSnapshotId
  }

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
  }

  fragment WorkspaceSensor on Sensor {
    id
    name
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
  ${PYTHON_ERROR_FRAGMENT}
  ${REPOSITORY_INFO_FRAGMENT}
  ${RESOURCE_ENTRY_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const CODE_LOCATION_STATUS_QUERY = gql`
  query CodeLocationStatusQuery {
    locationStatusesOrError {
      ... on WorkspaceLocationStatusEntries {
        entries {
          ...LocationStatusEntryFragment
        }
      }
    }
  }

  fragment LocationStatusEntryFragment on WorkspaceLocationStatusEntry {
    id
    name
    loadStatus
    updateTimestamp
    versionKey
  }
`;
