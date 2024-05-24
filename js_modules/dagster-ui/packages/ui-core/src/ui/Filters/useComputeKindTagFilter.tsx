import {Box, Icon} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {useStaticSetFilter} from './useStaticSetFilter';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';

const emptyArray: any[] = [];

export const useComputeKindTagFilter = ({
  allComputeKindTags,
  computeKindTags,
  setComputeKindTags,
}: {
  allComputeKindTags: string[];
  computeKindTags?: null | string[];
  setComputeKindTags?: null | ((s: string[]) => void);
}) => {
  return useStaticSetFilter<string>({
    name: 'Compute kind',
    icon: 'tag',
    allValues: useMemo(
      () =>
        allComputeKindTags.map((value) => ({
          value,
          match: [value],
        })),
      [allComputeKindTags],
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
};

export function useAssetKindTagsForAssets(
  assets: {definition?: {computeKind?: string | null} | null}[],
): string[] {
  return useMemo(
    () =>
      Array.from(
        new Set(assets.map((a) => a.definition?.computeKind).filter((x) => x)),
      ) as string[],
    [assets],
  );
}
