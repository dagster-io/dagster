import {Box, Icon} from '@dagster-io/ui-components';
import React, {useContext, useMemo} from 'react';

import {GraphNode} from './Utils';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {FeatureFlag, featureEnabled} from '../app/Flags';
import {AssetGroupSelector, ChangeReason} from '../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../nav/getLeftNavItemsForOption';
import {useFilters} from '../ui/Filters';
import {useCodeLocationFilter} from '../ui/Filters/useCodeLocationFilter';
import {FilterObject, FilterTag, FilterTagHighlightedText} from '../ui/Filters/useFilter';
import {useStaticSetFilter} from '../ui/Filters/useStaticSetFilter';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';

type OptionalFilters =
  | {
      assetGroups?: null;
      setGroupFilters?: null;
      visibleAssetGroups?: null;
      computeKindTags?: null;
      setComputeKindTags?: null;
      changedInBranch?: null;
      setChangedInBranch?: null;
    }
  | {
      assetGroups?: AssetGroupSelector[];
      visibleAssetGroups?: AssetGroupSelector[];
      setGroupFilters?: (groups: AssetGroupSelector[]) => void;
      computeKindTags?: string[];
      setComputeKindTags?: (s: string[]) => void;
      changedInBranch?: ChangeReason[];
      setChangedInBranch?: (s: ChangeReason[]) => void;
    };

type Props = {
  nodes: GraphNode[];
  clearExplorerPath: () => void;
  explorerPath: string;
  isGlobalGraph: boolean;
} & OptionalFilters;

const emptyArray: any[] = [];

export function useAssetGraphExplorerFilters({
  nodes,
  isGlobalGraph,
  assetGroups,
  visibleAssetGroups,
  setGroupFilters,
  computeKindTags,
  setComputeKindTags,
  explorerPath,
  clearExplorerPath,
  changedInBranch,
  setChangedInBranch,
}: Props) {
  const {allRepos} = useContext(WorkspaceContext);

  const reposFilter = useCodeLocationFilter();

  const changedFilter = useStaticSetFilter<ChangeReason>({
    name: 'Changed in branch',
    icon: 'new_in_branch',
    allValues: Object.values(ChangeReason).map((reason) => ({
      key: reason,
      value: reason,
      match: [reason],
    })),
    allowMultipleSelections: true,
    menuWidth: '300px',
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="new_in_branch" />
        <TruncatedTextWithFullTextOnHover
          tooltipText={value}
          text={
            <span style={{textTransform: 'capitalize'}}>
              {value.toLocaleLowerCase().replace('_', ' ')}
            </span>
          }
        />
      </Box>
    ),
    getStringValue: (value) => value[0] + value.slice(1).toLowerCase(),

    state: useMemo(() => new Set(changedInBranch ?? []), [changedInBranch]),
    onStateChanged: (values) => {
      if (setChangedInBranch) {
        setChangedInBranch(Array.from(values));
      }
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

    state: useMemo(() => new Set(visibleAssetGroups ?? []), [visibleAssetGroups]),
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
    state: computeKindTags ?? emptyArray,
    onStateChanged: (values) => {
      setComputeKindTags?.(Array.from(values));
    },
  });

  const filters: FilterObject[] = [];

  if (allRepos.length > 1 && isGlobalGraph) {
    filters.push(reposFilter);
  }
  if (assetGroups && setGroupFilters) {
    filters.push(groupsFilter);
  }
  const {isBranchDeployment} = React.useContext(CloudOSSContext);
  if (
    changedInBranch &&
    featureEnabled(FeatureFlag.flagExperimentalBranchDiff) &&
    isBranchDeployment
  ) {
    filters.push(changedFilter);
  }
  if (setComputeKindTags) {
    filters.push(kindTagsFilter);
  }
  const {button, activeFiltersJsx} = useFilters({filters});
  if (!filters.length) {
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
