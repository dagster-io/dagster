import {Box, Icon} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {COMMON_COLLATOR} from '../../app/Util';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {StaticBaseConfig, useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';

const emptyArray: any[] = [];

export const useKindFilter = ({
  allAssetKinds,
  kinds,
  setKinds,
}: {
  allAssetKinds: string[];
  kinds?: null | string[];
  setKinds?: null | ((s: string[]) => void);
}) => {
  return useStaticSetFilter<string>({
    ...BaseConfig,
    allValues: useMemo(
      () =>
        allAssetKinds.map((value) => ({
          value,
          match: [value],
        })),
      [allAssetKinds],
    ),
    menuWidth: '300px',
    state: kinds ?? emptyArray,
    onStateChanged: (values) => {
      setKinds?.(Array.from(values));
    },
    canSelectAll: true,
  });
};

export const getStringValue = (value: string) => value;

export const BaseConfig: StaticBaseConfig<string> = {
  name: 'Kind',
  icon: 'compute_kind',
  renderLabel: (value) => {
    return (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="compute_kind" />
        <TruncatedTextWithFullTextOnHover tooltipText={value.value} text={value.value} />
      </Box>
    );
  },
  getStringValue,
  getKey: getStringValue,
  matchType: 'all-of',
};

export function useAssetKindsForAssets(
  assets: {definition?: {kinds?: string[] | null} | null}[],
): string[] {
  return useMemo(
    () =>
      Array.from(new Set(assets.map((a) => a?.definition?.kinds || []).flat())).sort((a, b) =>
        COMMON_COLLATOR.compare(a, b),
      ),
    [assets],
  );
}
