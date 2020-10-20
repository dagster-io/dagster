import {Button, Menu, MenuItem, NonIdealState, Popover} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {Redirect, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components';

import {useRepositorySelector} from 'src/DagsterRepositoryContext';
import {Loading} from 'src/Loading';
import {explorerPathFromString} from 'src/PipelinePathUtils';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {PartitionView} from 'src/partitions/PartitionView';
import {PartitionsBackfill} from 'src/partitions/PartitionsBackfill';
import {
  PipelinePartitionsRootQuery,
  PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results,
} from 'src/partitions/types/PipelinePartitionsRootQuery';

type PartitionSet = PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results;

export const PipelinePartitionsRoot: React.FunctionComponent<RouteComponentProps<{
  pipelinePath: string;
}>> = ({match}) => {
  const {pipelineName, snapshotId} = explorerPathFromString(match.params.pipelinePath);
  useDocumentTitle(`Pipeline: ${pipelineName}`);

  const repositorySelector = useRepositorySelector();
  const queryResult = useQuery<PipelinePartitionsRootQuery>(PIPELINE_PARTITIONS_ROOT_QUERY, {
    variables: {repositorySelector, pipelineName},
    fetchPolicy: 'network-only',
    skip: !repositorySelector.repositoryLocationName || !repositorySelector.repositoryName,
  });
  const [selected, setSelected] = React.useState<PartitionSet | undefined>();
  const [runTags, setRunTags] = React.useState<{[key: string]: string}>({});

  if (snapshotId) {
    return <Redirect to={`/pipeline/${pipelineName}/partitions`} />;
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
            <PartitionSetSelector
              selected={partitionSet}
              partitionSets={partitionSetsOrError.results}
              onSelect={setSelected}
            />
            <PartitionsBackfill
              pipelineName={pipelineName}
              partitionSetName={partitionSet.name}
              onLaunch={(backfillId: string) => setRunTags({'dagster/backfill': backfillId})}
            />
            <PartitionView
              pipelineName={pipelineName}
              partitionSetName={partitionSet.name}
              runTags={runTags}
            />
          </PartitionRootContainer>
        );
      }}
    </Loading>
  );
};

const PartitionSetSelector: React.FunctionComponent<{
  selected: PartitionSet;
  partitionSets: PartitionSet[];
  onSelect: (partitionSet: PartitionSet) => void;
}> = ({partitionSets, selected, onSelect}) => {
  const [open, setOpen] = React.useState(false);
  const disabled = partitionSets.length <= 1;
  return (
    <Popover
      fill={true}
      isOpen={open}
      onInteraction={setOpen}
      minimal
      wrapperTagName="span"
      position={'bottom-left'}
      disabled={disabled}
      content={
        <Menu style={{minWidth: 280}}>
          {partitionSets.map((partitionSet, idx) => (
            <MenuItem
              key={idx}
              onClick={() => onSelect(partitionSet)}
              active={selected.name === partitionSet.name}
              icon={'git-repo'}
              text={<div>{partitionSet.name}</div>}
            />
          ))}
        </Menu>
      }
    >
      <Button text={selected.name} disabled={disabled} rightIcon="caret-down" />
    </Popover>
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
  padding: 30px;
  overflow-y: auto;
  min-height: calc(100vh - 45px);
`;
