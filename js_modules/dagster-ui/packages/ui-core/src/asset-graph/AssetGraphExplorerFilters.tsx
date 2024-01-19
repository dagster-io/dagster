import {Box, Icon} from '@dagster-io/ui-components';
import {useContext, useMemo} from 'react';

import {GraphNode} from './Utils';
import {AssetGroupSelector} from '../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../nav/getLeftNavItemsForOption';
import {useFilters} from '../ui/Filters';
import {FilterObject, FilterTag, FilterTagHighlightedText} from '../ui/Filters/useFilter';
import {useStaticSetFilter} from '../ui/Filters/useStaticSetFilter';
import {DagsterRepoOption, WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress, buildRepoPathForHuman} from '../workspace/buildRepoAddress';

const emptySet = new Set<any>();

type OptionalFilters =
  | {
      assetGroups?: null;
      setGroupFilters?: null;
      visibleAssetGroups?: null;
      computeKindTags?: null;
      setComputeKindTags?: null;
    }
  | {
      assetGroups: AssetGroupSelector[];
      visibleAssetGroups: AssetGroupSelector[];
      setGroupFilters: (groups: AssetGroupSelector[]) => void;
      computeKindTags: string[];
      setComputeKindTags: (s: string[]) => void;
    };

type Props = {
  nodes: GraphNode[];
  clearExplorerPath: () => void;
  explorerPath: string;
} & OptionalFilters;

const emptyArray: any[] = [];

export function useAssetGraphExplorerFilters({
  nodes,
  assetGroups,
  visibleAssetGroups,
  setGroupFilters,
  computeKindTags,
  setComputeKindTags,
  explorerPath,
  clearExplorerPath,
}: Props) {
  const {allRepos, visibleRepos, toggleVisible, setVisible} = useContext(WorkspaceContext);

  const visibleReposSet = useMemo(() => new Set(visibleRepos), [visibleRepos]);

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
    initialState: visibleReposSet.size === allRepos.length ? emptySet : visibleReposSet,
    onStateChanged: (values) => {
      let areAllVisible = false;
      if (values.size === 0) {
        areAllVisible = true;
      }
      allRepos.forEach((repo) => {
        const address = buildRepoAddress(repo.repository.name, repo.repositoryLocation.name);
        if (areAllVisible) {
          setVisible([address]);
        } else if (visibleReposSet.has(repo) !== values.has(repo)) {
          toggleVisible([address]);
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
    getTooltipText: (group) =>
      group.groupName +
      ' - ' +
      buildRepoPathForHuman(group.repositoryName, group.repositoryLocationName),

    initialState: useMemo(() => new Set(visibleAssetGroups ?? []), [visibleAssetGroups]),
    onStateChanged: (values) => {
      if (setGroupFilters) {
        setGroupFilters(Array.from(values));
      }
    },
  });

  const allKindTags = useMemo(
    () =>
      Array.from(
        new Set(nodes.map((node) => node.definition.computeKind).filter((v) => v) as string[]),
      ),
    [nodes],
  );

  const kindTagsFilter = useStaticSetFilter<string>({
    name: 'Compute kind',
    icon: 'tag',
    allValues: useMemo(
      () =>
        allKindTags.map((value) => ({
          value,
          match: [value],
        })),
      [allKindTags],
    ),
    menuWidth: '300px',
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="tag" />
        <TruncatedTextWithFullTextOnHover tooltipText={value} text={value} />
      </Box>
    ),
    getStringValue: (value) => value,
    initialState: computeKindTags ?? emptyArray,
    onStateChanged: (values) => {
      setComputeKindTags?.(Array.from(values));
    },
  });

  const filters: FilterObject[] = [];
  if (allRepos.length > 1) {
    filters.push(reposFilter);
  }
  if (assetGroups) {
    filters.push(groupsFilter);
  }
  filters.push(kindTagsFilter);
  const {button, activeFiltersJsx} = useFilters({filters});
  if (allRepos.length <= 1 && !assetGroups) {
    return {button: null, activeFiltersJsx: null};
  }
  return {
    button,
    filterBar:
      activeFiltersJsx.length || explorerPath ? (
        <Box padding={{vertical: 8, horizontal: 12}} flex={{gap: 12}}>
          {' '}
          {activeFiltersJsx}
          {explorerPath ? (
            <FilterTag
              label={
                <Box flex={{direction: 'row', alignItems: 'center'}}>
                  Asset selection is&nbsp;
                  <FilterTagHighlightedText tooltipText={explorerPath}>
                    {explorerPath}
                  </FilterTagHighlightedText>
                </Box>
              }
              onRemove={clearExplorerPath}
            />
          ) : null}
        </Box>
      ) : null,
  };
}
