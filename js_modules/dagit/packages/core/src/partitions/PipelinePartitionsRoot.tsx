import {gql, useQuery} from '@apollo/client';
import {Box, NonIdealState} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {explorerPathFromString, useStripSnapshotFromPath} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {Loading} from '../ui/Loading';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {PartitionView} from './PartitionView';
import {
  PipelinePartitionsRootQuery,
  PipelinePartitionsRootQueryVariables,
} from './types/PipelinePartitionsRootQuery';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelinePartitionsRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const params = useParams<{pipelinePath: string}>();
  const {pipelinePath} = params;

  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName} = explorerPath;

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  useJobTitle(explorerPath, isJob);
  useStripSnapshotFromPath(params);

  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<PipelinePartitionsRootQuery, PipelinePartitionsRootQueryVariables>(
    PIPELINE_PARTITIONS_ROOT_QUERY,
    {
      variables: {repositorySelector, pipelineName},
      fetchPolicy: 'network-only',
    },
  );

  return (
    <Loading queryResult={queryResult}>
      {({partitionSetsOrError}) => {
        if (partitionSetsOrError.__typename !== 'PartitionSets') {
          return (
            <Box padding={{vertical: 64}}>
              <NonIdealState
                icon="error"
                title="Partitions"
                description={partitionSetsOrError.message}
              />
            </Box>
          );
        }

        if (!partitionSetsOrError.results.length) {
          return (
            <Box padding={{vertical: 64}}>
              <NonIdealState
                icon="error"
                title="Partitions"
                description={
                  <p>
                    There are no partition sets defined for {isJob ? 'job' : 'pipeline'}{' '}
                    <code>{pipelineName}</code>.
                  </p>
                }
              />
            </Box>
          );
        }

        return (
          <PartitionView partitionSet={partitionSetsOrError.results[0]} repoAddress={repoAddress} />
        );
      }}
    </Loading>
  );
};

const PIPELINE_PARTITIONS_ROOT_QUERY = gql`
  query PipelinePartitionsRootQuery(
    $pipelineName: String!
    $repositorySelector: RepositorySelector!
  ) {
    partitionSetsOrError(pipelineName: $pipelineName, repositorySelector: $repositorySelector) {
      ... on PipelineNotFoundError {
        message
      }
      ...PythonErrorFragment
      ... on PartitionSets {
        results {
          id
          mode
          name
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
