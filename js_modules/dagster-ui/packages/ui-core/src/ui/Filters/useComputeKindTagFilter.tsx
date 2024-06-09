import {Box, Icon} from '@dagster-io/ui-components';
import uniqBy from 'lodash/uniqBy';
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
    icon: 'compute_kind',
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
        <Icon name="compute_kind" />
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
      uniqBy(
        assets.map((a) => a.definition?.computeKind).filter((x): x is string => !!x),
        (c) => c.toLowerCase(),
      ),
    [assets],
  );
}
