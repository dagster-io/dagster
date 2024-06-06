import {gql} from '@apollo/client';

import {REPOSITORY_INFO_FRAGMENT} from './RepositoryInformation';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {BASIC_INSTIGATION_STATE_FRAGMENT} from '../overview/BasicInstigationStateFragment';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';

export const LOCATION_WORKSPACE_QUERY = gql`
  query LocationWorkspaceQuery($name: String!) {
    workspaceLocationEntryOrError(name: $name) {
      ...WorkspaceLocationNode
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
      name
      isJob
      isAssetJob
      pipelineSnapshotId
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
      name
    }
    ...RepositoryInfoFragment
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
      selectorId
      status
    }
  }

  fragment WorkspaceSensor on Sensor {
    id
    jobOriginId
    name
    targets {
      mode
      pipelineName
    }
    sensorState {
      id
      selectorId
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
`;

export const CODE_LOCATION_STATUS_QUERY = gql`
  query CodeLocationStatusQuery {
    locationStatusesOrError {
      ... on WorkspaceLocationStatusEntries {
        entries {
          id
          name
          loadStatus
          updateTimestamp
        }
      }
    }
  }
`;
