import {gql, useApolloClient} from '@apollo/client';
import {Button, ButtonGroup, Colors, Icon} from '@blueprintjs/core';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from '../ui/Box';
import {DagsterRepoOption} from '../workspace/WorkspaceContext';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

import {tabForPipelinePathComponent} from './PipelineNav';
import {ContentListSolidsQuery} from './types/ContentListSolidsQuery';

interface RepositoryContentListProps {
  selector?: string;
  tab?: string;
  repos: DagsterRepoOption[];
  repoPath?: string;
}

type Item = {
  to: string;
  label: string;
  repoPath: string;
};

export const RepositoryContentList: React.FC<RepositoryContentListProps> = ({
  tab,
  repos,
  repoPath,
  selector,
}) => {
  const client = useApolloClient();
  const [type, setType] = React.useState<'pipelines' | 'solids'>('pipelines');
  const [selectedSolids, setSelectedSolids] = React.useState<Item[]>(() => []);

  const pipelineTab = tabForPipelinePathComponent(tab);

  React.useEffect(() => {
    if (type !== 'solids') {
      return;
    }

    const fetchSolids = async () => {
      const promises = repos.map((repo) =>
        client.query<ContentListSolidsQuery>({
          query: CONTENT_LIST_SOLIDS_QUERY,
          variables: {
            repositorySelector: {
              repositoryLocationName: repo.repositoryLocation.name,
              repositoryName: repo.repository.name,
            },
          },
        }),
      );

      const results = await Promise.all(promises);
      const allSolids: Item[] = Array.prototype.concat
        .apply(
          [],
          results.map((result) => {
            if (result.data.repositoryOrError.__typename === 'Repository') {
              const name = result.data.repositoryOrError.name;
              const location = result.data.repositoryOrError.location.name;
              const solids = result.data.repositoryOrError.usedSolids;
              return solids.map((solid) => ({
                to: workspacePath(name, location, `/solids/${solid.definition.name}`),
                label: solid.definition.name,
                repoPath: buildRepoPath(name, location),
              }));
            }
            return [];
          }),
        )
        .sort((a: Item, b: Item) =>
          a.label.toLocaleLowerCase().localeCompare(b.label.toLocaleLowerCase()),
        );

      setSelectedSolids(allSolids);
    };

    fetchSolids();
  }, [client, repos, type]);

  const selectedPipelines = React.useMemo(() => {
    return repos
      .reduce(
        (accum, repo) => [
          ...accum,
          ...repo.repository.pipelines
            .map((pipeline) => pipeline.name)
            .map((p) => ({
              to: workspacePath(
                repo.repository.name,
                repo.repositoryLocation.name,
                `/pipelines/${p}/${tab === 'partitions' ? 'overview' : pipelineTab.pathComponent}`,
              ),
              label: p,
              repoPath: buildRepoPath(repo.repository.name, repo.repositoryLocation.name),
            })),
        ],
        [] as Item[],
      )
      .sort((a, b) => a.label.toLocaleLowerCase().localeCompare(b.label.toLocaleLowerCase()));
  }, [pipelineTab.pathComponent, repos, tab]);

  const items = type === 'pipelines' ? selectedPipelines : selectedSolids;

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
            key={p.to}
            data-tooltip={p.label}
            data-tooltip-style={p.label === selector ? SelectedItemTooltipStyle : ItemTooltipStyle}
            className={`${p.label === selector && p.repoPath === repoPath ? 'selected' : ''}`}
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
        name
        location {
          id
          name
        }
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
