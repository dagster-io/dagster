import * as React from 'react';

import {useStaticSetFilter} from './useStaticSetFilter';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {WorkspaceContext} from '../../workspace/WorkspaceContext';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../../workspace/repoAddressAsString';
import {RepoAddress} from '../../workspace/types';

export const useCodeLocationFilter = () => {
  const {allRepos, visibleRepos, setVisible, setHidden} = React.useContext(WorkspaceContext);

  const allRepoAddresses = React.useMemo(() => {
    return allRepos.map((repo) =>
      buildRepoAddress(repo.repository.name, repo.repositoryLocation.name),
    );
  }, [allRepos]);

  const visibleRepoAddresses = React.useMemo(() => {
    return visibleRepos.length === allRepos.length
      ? []
      : visibleRepos.map((repo) =>
          buildRepoAddress(repo.repository.name, repo.repositoryLocation.name),
        );
  }, [allRepos, visibleRepos]);

  return useStaticSetFilter<RepoAddress>({
    name: 'Code location',
    icon: 'folder',
    initialState: visibleRepoAddresses,
    allValues: allRepoAddresses.map((repoAddress) => {
      return {value: repoAddress, match: [repoAddressAsHumanString(repoAddress)]};
    }),
    getKey: (repoAddress) => repoAddressAsHumanString(repoAddress),
    renderLabel: ({value}) => (
      <TruncatedTextWithFullTextOnHover text={repoAddressAsHumanString(value)} />
    ),
    getStringValue: (value) => repoAddressAsHumanString(value),
    onStateChanged: (state: Set<RepoAddress>) => {
      if (state.size === 0) {
        setVisible(allRepoAddresses);
        return;
      }

      const hidden = allRepoAddresses.filter((repoAddress) => !state.has(repoAddress));
      setHidden(hidden);
      setVisible(Array.from(state));
    },
    menuWidth: '500px',
  });
};
