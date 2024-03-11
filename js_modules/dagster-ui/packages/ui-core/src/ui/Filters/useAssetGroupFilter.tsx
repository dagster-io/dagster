import {Box, Icon} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {useStaticSetFilter} from './useStaticSetFilter';
import {AssetGroupSelector} from '../../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';

export const useAssetGroupFilter = ({
  assetGroups,
  visibleAssetGroups,
  setGroupFilters,
}: {
  assetGroups?: AssetGroupSelector[] | null;
  visibleAssetGroups?: AssetGroupSelector[] | null;
  setGroupFilters?: null | ((groups: AssetGroupSelector[]) => void);
}) => {
  return useStaticSetFilter<AssetGroupSelector>({
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
};
