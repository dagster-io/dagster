import {Box, Icon} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {buildDefinitionTag} from './useAssetTagFilter';
import {useStaticSetFilter} from './useStaticSetFilter';
import {DefinitionTag} from '../../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';

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
    name: 'Storage kind',
    icon: 'tag',
    allValues: useMemo(
      () =>
        allAssetStorageKindTags.map((value) => ({
          value,
          match: [value.key + ':' + value.value],
        })),
      [allAssetStorageKindTags],
    ),
    menuWidth: '300px',
    renderLabel: ({value: tag}) => {
      return (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="tag" />
          <TruncatedTextWithFullTextOnHover tooltipText={tag.value} text={tag.value} />
        </Box>
      );
    },
    getStringValue: ({value}) => value,
    state: memoizedState ?? emptyArray,
    onStateChanged: (values) => {
      setStorageKindTags?.(Array.from(values));
    },
    matchType: 'all-of',
    canSelectAll: false,
  });
};
