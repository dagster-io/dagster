import {Box, Icon} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {buildDefinitionTag} from './useAssetTagFilter';
import {DefinitionTag} from '../../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {StaticBaseConfig, useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';

const emptyArray: any[] = [];

export const useStorageKindFilter = ({
  allAssetStorageKindTags,
  storageKindTags,
  setStorageKindTags,
}: {
  allAssetStorageKindTags: DefinitionTag[];
  storageKindTags?: null | DefinitionTag[];
  setStorageKindTags?: null | ((s: DefinitionTag[]) => void);
}) => {
  const memoizedState = useMemo(() => storageKindTags?.map(buildDefinitionTag), [storageKindTags]);
  return useStaticSetFilter<DefinitionTag>({
    allValues: useMemo(
      () =>
        allAssetStorageKindTags.map((value) => ({
          value,
          match: [value.key + ':' + value.value],
        })),
      [allAssetStorageKindTags],
    ),
    menuWidth: '300px',
    state: memoizedState ?? emptyArray,
    onStateChanged: (values) => {
      setStorageKindTags?.(Array.from(values));
    },
    canSelectAll: false,
    ...BaseConfig,
  });
};

export const getStringValue = ({value}: DefinitionTag) => value;

export const BaseConfig: StaticBaseConfig<DefinitionTag> = {
  name: 'Storage kind',
  icon: 'storage_kind',
  renderLabel: ({value: tag}: {value: DefinitionTag}) => {
    return (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="storage_kind" />
        <TruncatedTextWithFullTextOnHover tooltipText={tag.value} text={tag.value} />
      </Box>
    );
  },
  getStringValue,
  getKey: getStringValue,
  matchType: 'all-of',
};
