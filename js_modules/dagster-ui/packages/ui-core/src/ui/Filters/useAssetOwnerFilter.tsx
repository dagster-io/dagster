import memoize from 'lodash/memoize';
import {useMemo} from 'react';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';

import {assertUnreachable} from '../../app/Util';
import {AssetOwner} from '../../graphql/types';
import {StaticBaseConfig, useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';

const emptyArray: any[] = [];

export const useAssetOwnerFilter = ({
  allAssetOwners,
  owners,
  setOwners,
}: {
  allAssetOwners: AssetOwner[];
  owners?: null | AssetOwner[] | string[];
  setOwners?: null | ((s: AssetOwner[]) => void);
}) => {
  const memoizedState = useMemo(() => {
    return owners
      ?.map((owner) => {
        if (typeof owner !== 'string') {
          return memoizedOwner(owner);
        }
        const typedOwner = allAssetOwners.find((typedOwner) => {
          if ('team' in typedOwner) {
            return typedOwner.team === owner;
          } else if ('email' in typedOwner) {
            return typedOwner.email === owner;
          } else {
            assertUnreachable(typedOwner);
          }
        });
        if (!typedOwner) {
          return null;
        }
        return memoizedOwner(typedOwner);
      })
      .filter((o) => o);
  }, [allAssetOwners, owners]);
  return useStaticSetFilter<AssetOwner>({
    ...BaseConfig,
    allValues: useMemo(
      () =>
        allAssetOwners.map((value) => ({
          value,
          match: [stringValueFromOwner(value)],
        })),
      [allAssetOwners],
    ),
    menuWidth: '300px',
    state: memoizedState ?? emptyArray,
    onStateChanged: (values) => {
      setOwners?.(Array.from(values));
    },
  });
};

export function useAssetOwnersForAssets(
  assets: {
    definition?: {
      owners?: AssetOwner[] | null;
    } | null;
  }[],
): AssetOwner[] {
  return useMemo(() => {
    return Array.from(
      new Set(
        assets
          .flatMap((a) => a.definition?.owners)
          .filter((o) => o)
          // Convert to JSON for deduping by Set
          .map((owner) => JSON.stringify(owner)),
      ),
      // Convert back to AssetOwner
    ).map((ownerJSON) => memoizedOwner(JSON.parse(ownerJSON)));
  }, [assets]);
}

const memoizedOwner = memoize(
  (owner: AssetOwner) => {
    return owner;
  },
  (owner) => JSON.stringify(owner),
);

function stringValueFromOwner(owner: AssetOwner) {
  const typename = owner.__typename;
  switch (typename) {
    case 'TeamAssetOwner':
      return owner.team;
    case 'UserAssetOwner':
      return owner.email;
    default:
      assertUnreachable(typename);
  }
}

export const BaseConfig: StaticBaseConfig<AssetOwner> = {
  name: 'Owner',
  icon: 'account_circle',
  renderLabel: ({value}: {value: AssetOwner}) => (
    <UserDisplay email={stringValueFromOwner(value)} isFilter={true} />
  ),
  getStringValue: (value: AssetOwner) => stringValueFromOwner(value),
};
