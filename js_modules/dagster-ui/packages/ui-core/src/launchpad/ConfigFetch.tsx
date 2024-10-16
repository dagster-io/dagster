import {ApolloClient, gql} from '../apollo-client';
import {
  ConfigPartitionForAssetJobQuery,
  ConfigPartitionForAssetJobQueryVariables,
  ConfigPartitionSelectionQuery,
  ConfigPartitionSelectionQueryVariables,
} from './types/ConfigFetch.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';

export async function fetchTagsAndConfigForJob(
  client: ApolloClient<any>,
  variables: ConfigPartitionSelectionQueryVariables,
) {
  const {data} = await client.query<
    ConfigPartitionSelectionQuery,
    ConfigPartitionSelectionQueryVariables
  >({
    query: CONFIG_PARTITION_SELECTION_QUERY,
    variables,
  });

  if (
    !data ||
    !data.partitionSetOrError ||
    data.partitionSetOrError.__typename !== 'PartitionSet' ||
    !data.partitionSetOrError.partition
  ) {
    return;
  }

  const {partition} = data.partitionSetOrError;

  if (partition.tagsOrError.__typename === 'PythonError') {
    showCustomAlert({
      title: 'Unable to load tags',
      body: <PythonErrorInfo error={partition.tagsOrError} />,
    });
    return;
  }
  if (partition.runConfigOrError.__typename === 'PythonError') {
    showCustomAlert({
      title: 'Unable to load tags',
      body: <PythonErrorInfo error={partition.runConfigOrError} />,
    });
    return;
  }

  return {
    yaml: partition.runConfigOrError.yaml,
    tags: partition.tagsOrError.results.map((t) => ({key: t.key, value: t.value})),
    solidSelection: partition.solidSelection,
    mode: partition.mode,
  };
}

export async function fetchTagsAndConfigForAssetJob(
  client: ApolloClient<any>,
  variables: ConfigPartitionForAssetJobQueryVariables,
) {
  const {data: tagAndConfigData} = await client.query<
    ConfigPartitionForAssetJobQuery,
    ConfigPartitionForAssetJobQueryVariables
  >({
    query: CONFIG_PARTITION_FOR_ASSET_JOB_QUERY,
    fetchPolicy: 'network-only',
    variables,
  });

  if (
    !tagAndConfigData ||
    !tagAndConfigData.pipelineOrError ||
    tagAndConfigData.pipelineOrError.__typename !== 'Pipeline' ||
    !tagAndConfigData.pipelineOrError.partition
  ) {
    return;
  }

  const {partition} = tagAndConfigData.pipelineOrError;

  if (partition.tagsOrError.__typename === 'PythonError') {
    showCustomAlert({
      title: 'Unable to load tags',
      body: <PythonErrorInfo error={partition.tagsOrError} />,
    });
    return;
  }
  if (partition.runConfigOrError.__typename === 'PythonError') {
    showCustomAlert({
      title: 'Unable to load tags',
      body: <PythonErrorInfo error={partition.runConfigOrError} />,
    });
    return;
  }

  return {
    yaml: partition.runConfigOrError.yaml,
    tags: partition.tagsOrError.results.map((t) => ({key: t.key, value: t.value})),
    solidSelection: null,
    mode: null,
  };
}

export const CONFIG_PARTITION_FOR_ASSET_JOB_QUERY = gql`
  query ConfigPartitionForAssetJobQuery(
    $repositoryName: String!
    $repositoryLocationName: String!
    $jobName: String!
    $partitionName: String!
    $assetKeys: [AssetKeyInput!]!
  ) {
    pipelineOrError(
      params: {
        pipelineName: $jobName
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
      }
    ) {
      ... on Pipeline {
        id
        partition(partitionName: $partitionName, selectedAssetKeys: $assetKeys) {
          name
          runConfigOrError {
            ... on PartitionRunConfig {
              yaml
            }
            ...PythonErrorFragment
          }
          tagsOrError {
            ... on PartitionTags {
              results {
                key
                value
              }
            }
            ...PythonErrorFragment
          }
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const CONFIG_PARTITION_SELECTION_QUERY = gql`
  query ConfigPartitionSelectionQuery(
    $repositorySelector: RepositorySelector!
    $partitionSetName: String!
    $partitionName: String!
  ) {
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      ... on PartitionSet {
        id
        partition(partitionName: $partitionName) {
          name
          solidSelection
          runConfigOrError {
            ... on PartitionRunConfig {
              yaml
            }
            ...PythonErrorFragment
          }
          mode
          tagsOrError {
            ... on PartitionTags {
              results {
                key
                value
              }
            }
            ...PythonErrorFragment
          }
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
