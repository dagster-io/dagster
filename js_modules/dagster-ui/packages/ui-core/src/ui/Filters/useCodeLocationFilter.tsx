import {useCallback, useContext, useMemo} from 'react';

import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {WorkspaceContext} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../../workspace/repoAddressAsString';
import {RepoAddress} from '../../workspace/types';
import {StaticBaseConfig, useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';

type Props =
  | {
      codeLocations: RepoAddress[];
      setCodeLocations: (repos: RepoAddress[]) => void;
    }
  | {
      codeLocations: undefined;
      setCodeLocations: undefined;
    };

/**
 * If props are passed that this filter is in "controlled mode" (you tell it what the current state is)
 *
 * Otherwise it's uncontrolled and uses WorkspaceContext to control the current state
 * This means that any logic depending on the state of this filter would need to read
 * WorkspaceContext to get the current state.
 */
export const useCodeLocationFilter = (
  {codeLocations, setCodeLocations}: Props = {
    codeLocations: undefined,
    setCodeLocations: undefined,
  },
) => {
  const {allRepos, visibleRepos, setVisible, setHidden} = useContext(WorkspaceContext);

  const allRepoAddresses = useMemo(() => {
    return allRepos.map((repo) =>
      buildRepoAddress(repo.repository.name, repo.repositoryLocation.name),
    );
  }, [allRepos]);

  const visibleRepoAddresses = useMemo(() => {
    return visibleRepos.length === allRepos.length
      ? []
      : visibleRepos.map((repo) =>
          buildRepoAddress(repo.repository.name, repo.repositoryLocation.name),
        );
  }, [allRepos, visibleRepos]);

  const setVisibleRepos = useCallback(
    (state: Set<RepoAddress>) => {
      if (state.size === 0) {
        setVisible(allRepoAddresses);
        return;
      }

      const hidden = allRepoAddresses.filter((repoAddress) => !state.has(repoAddress));
      setHidden(hidden);
      setVisible(Array.from(state));
    },
    [allRepoAddresses, setHidden, setVisible],
  );

  return useStaticSetFilter<RepoAddress>({
    state: codeLocations ? codeLocations : visibleRepoAddresses,
    allValues: useMemo(
      () =>
        allRepoAddresses.map((repoAddress) => {
          return {value: repoAddress, match: [repoAddressAsHumanString(repoAddress)]};
        }),
      [allRepoAddresses],
    ),
    onStateChanged: (state) => {
      if (setCodeLocations) {
        setCodeLocations(Array.from(state));
      } else {
        setVisibleRepos(state);
      }
    },
    menuWidth: '500px',
    ...BaseConfig,
  });
};

const getStringValue = (value: RepoAddress) => repoAddressAsHumanString(value);

export const BaseConfig: StaticBaseConfig<RepoAddress> = {
  name: 'Code location',
  icon: 'folder',
  renderLabel: ({value}: {value: RepoAddress}) => (
    <TruncatedTextWithFullTextOnHover text={repoAddressAsHumanString(value)} />
  ),
  getStringValue,
  getKey: getStringValue,
};
