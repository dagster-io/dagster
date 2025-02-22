import {Box, Icon, IconName} from '@dagster-io/ui-components';
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
  // Sort asset kinds with prioritized kinds first
  const sortedAssetKinds = useMemo(() => {
    // Define prioritized kinds
    const prioritizedKinds = ['python', 'bigquery', 'gcs'];
    return [
      ...prioritizedKinds,
      ...allAssetKinds.filter((kind) => !prioritizedKinds.includes(kind)).sort((a, b) => COMMON_COLLATOR.compare(a, b)),
    ];
  }, [allAssetKinds]);

  return useStaticSetFilter<string>({
    ...BaseConfig,
    allValues: useMemo(
      () =>
        sortedAssetKinds.map((value) => ({
          value,
          match: [value],
        })),
      [sortedAssetKinds],
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
    // Define custom icons or emojis for specific kinds
    const customIcons: {[key: string]: IconName | string} = {

      // icons pulled from icon.tsx
      python: 'code_block', // Emoji for python
      bigquery: 'graph', // Emoji for bigquery
      gcs: 'cloud', // Emoji for gcs
      bug: 'bug',
      calendar: 'calendar' 

      // Add more custom icons or emojis here
    };

    // Use custom icon or emoji if available, otherwise default to 'compute_kind'
    const icon = customIcons[value.value] || 'compute_kind';

    return (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        {typeof icon === 'string' ? <span>{icon}</span> : <Icon name={icon} />}
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