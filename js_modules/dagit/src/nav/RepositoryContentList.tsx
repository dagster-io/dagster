import {gql, useLazyQuery} from '@apollo/client';
import {Button, ButtonGroup, Colors, Icon} from '@blueprintjs/core';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {tabForPipelinePathComponent} from 'src/nav/PipelineNav';
import {ContentListSolidsQuery} from 'src/nav/types/ContentListSolidsQuery';
import {Box} from 'src/ui/Box';
import {DagsterRepoOption} from 'src/workspace/WorkspaceContext';
import {workspacePath} from 'src/workspace/workspacePath';

interface RepositoryContentListProps {
  selector?: string;
  tab?: string;
  repo: DagsterRepoOption;
}

export const RepositoryContentList: React.FunctionComponent<RepositoryContentListProps> = ({
  tab,
  repo,
  selector,
}) => {
  const [type, setType] = React.useState<'pipelines' | 'solids'>('pipelines');
  const pipelineTab = tabForPipelinePathComponent(tab);
  const repoName = repo.repository.name;
  const repoLocation = repo.repositoryLocation.name;

  // Load solids, but only if the user clicks on the Solid option
  const [fetchSolids, solids] = useLazyQuery<ContentListSolidsQuery>(CONTENT_LIST_SOLIDS_QUERY, {
    fetchPolicy: 'cache-first',
    variables: {
      repositorySelector: {
        repositoryLocationName: repo.repositoryLocation.name,
        repositoryName: repo.repository.name,
      },
    },
  });

  React.useEffect(() => {
    if (type === 'solids') {
      fetchSolids();
    }
  }, [type, fetchSolids]);

  const usedSolids =
    solids.data?.repositoryOrError?.__typename === 'Repository'
      ? solids.data.repositoryOrError.usedSolids
      : [];

  const items =
    type === 'pipelines'
      ? repo.repository.pipelines
          .map((pipeline) => pipeline.name)
          .map((p) => ({
            to: workspacePath(
              repoName,
              repoLocation,
              `/pipelines/${p}/${tab === 'partitions' ? 'overview' : pipelineTab.pathComponent}`,
            ),
            label: p,
          }))
      : usedSolids.map(({definition}) => ({
          to: workspacePath(repoName, repoLocation, `/solids/${definition.name}`),
          label: definition.name,
        }));

  return (
    <Box flex={{direction: 'column'}} style={{minHeight: 0, flex: 1}}>
      <Box
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        padding={{vertical: 8, horizontal: 12}}
        border={{side: 'bottom', width: 1, color: Colors.DARK_GRAY3}}
      >
        <ItemHeader>{'Pipelines & Solids'}</ItemHeader>
        <ButtonGroup>
          <Button
            small={true}
            active={type === 'pipelines'}
            intent={type === 'pipelines' ? 'primary' : 'none'}
            icon={<Icon icon="diagram-tree" iconSize={13} />}
            onClick={() => setType('pipelines')}
          />
          <Button
            small={true}
            active={type === 'solids'}
            intent={type === 'solids' ? 'primary' : 'none'}
            icon={<Icon icon="git-commit" iconSize={13} />}
            onClick={() => setType('solids')}
          />
        </ButtonGroup>
      </Box>
      <Items>
        {items.map((p) => (
          <Item
            key={p.label}
            data-tooltip={p.label}
            data-tooltip-style={p.label === selector ? SelectedItemTooltipStyle : ItemTooltipStyle}
            className={`${p.label === selector ? 'selected' : ''}`}
            to={p.to}
          >
            {p.label}
          </Item>
        ))}
      </Items>
    </Box>
  );
};

const ItemHeader = styled.div`
  font-size: 15px;
  text-overflow: ellipsis;
  overflow: hidden;
  font-weight: bold;
  color: ${Colors.LIGHT_GRAY3} !important;
`;

const Items = styled.div`
  flex: 1;
  overflow: auto;
  &::-webkit-scrollbar {
    width: 11px;
  }

  scrollbar-width: thin;
  scrollbar-color: ${Colors.GRAY1} ${Colors.DARK_GRAY1};

  &::-webkit-scrollbar-track {
    background: ${Colors.DARK_GRAY1};
  }
  &::-webkit-scrollbar-thumb {
    background-color: ${Colors.GRAY1};
    border-radius: 6px;
    border: 3px solid ${Colors.DARK_GRAY1};
  }
`;

const Item = styled(Link)`
  font-size: 13px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 8px 12px;
  padding-left: 8px;
  border-left: 4px solid transparent;
  border-bottom: 1px solid transparent;
  display: block;
  color: ${Colors.LIGHT_GRAY3} !important;
  &:hover {
    text-decoration: none;
    color: ${Colors.WHITE} !important;
  }
  &:focus {
    outline: 0;
  }
  &.focused {
    border-left: 4px solid ${Colors.GRAY3};
  }
  &.selected {
    border-left: 4px solid ${Colors.COBALT3};
    border-bottom: 1px solid ${Colors.DARK_GRAY2};
    background: ${Colors.BLACK};
    font-weight: 600;
    color: ${Colors.WHITE} !important;
  }
`;

const BaseTooltipStyle = {
  fontSize: 13,
  padding: 3,
  paddingRight: 7,
  left: 9,
  top: 5,
  color: Colors.WHITE,
  background: Colors.DARK_GRAY1,
  transform: 'none',
  border: 0,
  borderRadius: 4,
};

const ItemTooltipStyle = JSON.stringify({
  ...BaseTooltipStyle,
  color: Colors.WHITE,
  background: Colors.DARK_GRAY1,
});

const SelectedItemTooltipStyle = JSON.stringify({
  ...BaseTooltipStyle,
  color: Colors.WHITE,
  background: Colors.BLACK,
  fontWeight: 600,
});

const CONTENT_LIST_SOLIDS_QUERY = gql`
  query ContentListSolidsQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolids {
          __typename
          definition {
            name
          }
          invocations {
            __typename
            pipeline {
              id
              name
            }
          }
        }
      }
    }
  }
`;
