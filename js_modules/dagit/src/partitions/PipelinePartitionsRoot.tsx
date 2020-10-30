import {gql, useQuery} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Redirect} from 'react-router-dom';
import styled from 'styled-components';

import {Loading} from 'src/Loading';
import {explorerPathFromString} from 'src/PipelinePathUtils';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {PartitionView} from 'src/partitions/PartitionView';
import {
  PipelinePartitionsRootQuery,
  PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results,
  PipelinePartitionsRootQueryVariables,
} from 'src/partitions/types/PipelinePartitionsRootQuery';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

type PartitionSet = PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results;

interface Props {
  pipelinePath: string;
  repoAddress: RepoAddress;
}

export const PipelinePartitionsRoot: React.FC<Props> = (props) => {
  const {pipelinePath, repoAddress} = props;
  const {pipelineName, snapshotId} = explorerPathFromString(pipelinePath);
  useDocumentTitle(`Pipeline: ${pipelineName}`);
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<PipelinePartitionsRootQuery, PipelinePartitionsRootQueryVariables>(
    PIPELINE_PARTITIONS_ROOT_QUERY,
    {
      variables: {repositorySelector, pipelineName},
      fetchPolicy: 'network-only',
    },
  );
  const [selected, setSelected] = React.useState<PartitionSet | undefined>();

  if (snapshotId) {
    return (
      <Redirect
        to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/partitions`)}
      />
    );
  }

  return (
    <Loading queryResult={queryResult}>
      {({partitionSetsOrError}) => {
        if (partitionSetsOrError.__typename !== 'PartitionSets') {
          return (
            <Wrapper>
              <NonIdealState
                icon="multi-select"
                title="Partitions"
                description={partitionSetsOrError.message}
              />
            </Wrapper>
          );
        }

        if (!partitionSetsOrError.results.length) {
          return (
            <Wrapper>
              <NonIdealState
                icon="multi-select"
                title="Partitions"
                description={
                  <p>
                    There are no partition sets defined for pipeline <code>{pipelineName}</code>.
                  </p>
                }
              />
            </Wrapper>
          );
        }

        const selectionHasMatch =
          selected && !!partitionSetsOrError.results.filter((x) => x.name === selected.name).length;
        const partitionSet =
          selectionHasMatch && selected ? selected : partitionSetsOrError.results[0];

        return (
          <PartitionRootContainer>
            <PartitionView
              partitionSet={partitionSet}
              partitionSets={partitionSetsOrError.results}
              onChangePartitionSet={setSelected}
              pipelineName={pipelineName}
              repoAddress={repoAddress}
            />
          </PartitionRootContainer>
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
      ... on PythonError {
        message
      }
      ... on PartitionSets {
        results {
          name
        }
      }
    }
  }
`;

const Wrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  overflow: auto;
`;

const PartitionRootContainer = styled.div`
  padding: 15px;
  overflow-y: auto;
  min-height: calc(100vh - 45px);
`;
