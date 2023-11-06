import {Box, Icon} from '@dagster-io/ui-components';
import React from 'react';

import {AssetGroupSelector} from '../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../nav/getLeftNavItemsForOption';
import {useFilters} from '../ui/Filters';
import {FilterObject} from '../ui/Filters/useFilter';
import {useStaticSetFilter} from '../ui/Filters/useStaticSetFilter';
import {DagsterRepoOption, WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress, buildRepoPathForHuman} from '../workspace/buildRepoAddress';

export const AssetGraphExplorerFilters = React.memo(
  ({
    assetGroups,
    visibleAssetGroups,
    setGroupFilters,
  }:
    | {
        assetGroups: AssetGroupSelector[];
        visibleAssetGroups: AssetGroupSelector[];
        setGroupFilters: (groups: AssetGroupSelector[]) => void;
      }
    | {assetGroups?: null; setGroupFilters?: null; visibleAssetGroups?: null}) => {
    const {allRepos, visibleRepos, toggleVisible} = React.useContext(WorkspaceContext);

    const visibleReposSet = React.useMemo(() => new Set(visibleRepos), [visibleRepos]);

    const reposFilter = useStaticSetFilter<DagsterRepoOption>({
      name: 'Code location',
      icon: 'repo',
      allValues: allRepos.map((repo) => ({
        key: repo.repository.id,
        value: repo,
        match: [buildRepoPathForHuman(repo.repository.name, repo.repositoryLocation.name)],
      })),
      menuWidth: '300px',
      renderLabel: ({value}) => (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="repo" />
          <TruncatedTextWithFullTextOnHover
            text={buildRepoPathForHuman(value.repository.name, value.repositoryLocation.name)}
          />
        </Box>
      ),
      getStringValue: (value) =>
        buildRepoPathForHuman(value.repository.name, value.repositoryLocation.name),
      initialState: visibleReposSet,
      onStateChanged: (values) => {
        allRepos.forEach((repo) => {
          if (visibleReposSet.has(repo) !== values.has(repo)) {
            toggleVisible([buildRepoAddress(repo.repository.name, repo.repositoryLocation.name)]);
          }
        });
      },
    });

    const groupsFilter = useStaticSetFilter<AssetGroupSelector>({
      name: 'Asset Groups',
      icon: 'asset_group',
      allValues: (assetGroups || []).map((group) => ({
        key: group.groupName,
        value:
          visibleAssetGroups?.find(
            (visibleGroup) =>
              visibleGroup.groupName === group.groupName &&
              visibleGroup.repositoryName === group.repositoryName &&
              visibleGroup.repositoryLocationName === group.repositoryLocationName,
          ) ?? group,
        match: [group.groupName],
      })),
      menuWidth: '300px',
      renderLabel: ({value}) => (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="repo" />
          <TruncatedTextWithFullTextOnHover
            tooltipText={
              value.groupName +
              ' - ' +
              buildRepoPathForHuman(value.repositoryName, value.repositoryLocationName)
            }
            text={
              <>
                {value.groupName}
                <span style={{opacity: 0.5, paddingLeft: '4px'}}>
                  {buildRepoPathForHuman(value.repositoryName, value.repositoryLocationName)}
                </span>
              </>
            }
          />
        </Box>
      ),
      getStringValue: (group) => group.groupName,
      initialState: React.useMemo(() => new Set(visibleAssetGroups ?? []), [visibleAssetGroups]),
      onStateChanged: (values) => {
        if (setGroupFilters) {
          setGroupFilters(Array.from(values));
        }
      },
    });

    const filters: FilterObject[] = [];
    if (allRepos.length > 1) {
      filters.push(reposFilter);
    }
    if (assetGroups) {
      filters.push(groupsFilter);
    }
    const {button} = useFilters({filters});
    if (allRepos.length <= 1 && !assetGroups) {
      return null;
    }
    return button;
  },
);
