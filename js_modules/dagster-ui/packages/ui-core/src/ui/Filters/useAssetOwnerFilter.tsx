import {Box, Icon} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {useStaticSetFilter} from './useStaticSetFilter';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';

const emptyArray: any[] = [];

export const useAssetOwnerFilter = ({
  allAssetOwners,
  owners,
  setOwners,
}: {
  allAssetOwners: string[];
  owners?: null | string[];
  setOwners?: null | ((s: string[]) => void);
}) => {
  return useStaticSetFilter<string>({
    name: 'Owner',
    icon: 'account_circle',
    allValues: useMemo(
      () =>
        allAssetOwners.map((value) => ({
          value,
          match: [value],
        })),
      [allAssetOwners],
    ),
    menuWidth: '300px',
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="account_circle" />
        <TruncatedTextWithFullTextOnHover tooltipText={value} text={value} />
      </Box>
    ),
    getStringValue: (value) => value,
    state: owners ?? emptyArray,
    onStateChanged: (values) => {
      setOwners?.(Array.from(values));
    },
  });
};

export function useAssetOwnersForAssets(
  assets: {
    definition?: {
      owners: Array<
        {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
      >;
    } | null;
  }[],
): string[] {
  return useMemo(
    () =>
      Array.from(
        new Set(
          assets.flatMap(
            (a) =>
              a.definition?.owners.flatMap((o) =>
                o.__typename === 'TeamAssetOwner' ? o.team : o.email,
              ),
          ),
        ),
      ) as string[],
    [assets],
  );
}
