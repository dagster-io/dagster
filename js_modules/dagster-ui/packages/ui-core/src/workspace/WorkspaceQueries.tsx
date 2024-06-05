import {gql} from '@apollo/client';

import {REPOSITORY_INFO_FRAGMENT} from './RepositoryInformation';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

export const LOCATION_WORKSPACE_QUERY = gql`
  query LocationWorkspaceQuery($name: String!) {
    workspaceLocationEntryOrError(name: $name) {
      __typename
      ... on WorkspaceLocationEntry {
        id
        name
        loadStatus
        displayMetadata {
          key
          value
        }
        updatedTimestamp
        featureFlags {
          name
          enabled
        }
        locationOrLoadError {
          ... on RepositoryLocation {
            id
            name
            dagsterLibraryVersions {
              name
              version
            }
            repositories {
              ...RepositoryInfoFragment
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
                name
                cronSchedule
                executionTimezone
                mode
                pipelineName
                scheduleState {
                  id
                  selectorId
                  status
                }
              }
              sensors {
                id
                name
                jobOriginId
                targets {
                  mode
                  pipelineName
                }
                sensorState {
                  id
                  selectorId
                  status
                }
                sensorType
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
            }
          }
          ...PythonErrorFragment
        }
      }
    }
  }
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
