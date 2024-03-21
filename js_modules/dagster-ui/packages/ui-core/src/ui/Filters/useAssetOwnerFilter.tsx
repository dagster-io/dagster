import memoize from 'lodash/memoize';
import {useMemo} from 'react';

import {useStaticSetFilter} from './useStaticSetFilter';
import {assertUnreachable} from '../../app/Util';
import {AssetOwner} from '../../graphql/types';
import {useLaunchPadHooks} from '../../launchpad/LaunchpadHooksContext';

const emptyArray: any[] = [];

export const useAssetOwnerFilter = ({
  allAssetOwners,
  owners,
  setOwners,
}: {
  allAssetOwners: AssetOwner[];
  owners?: null | AssetOwner[];
  setOwners?: null | ((s: AssetOwner[]) => void);
}) => {
  const memoizedState = useMemo(() => owners?.map(memoizedOwner), [owners]);
  const {UserDisplay} = useLaunchPadHooks();
  return useStaticSetFilter<AssetOwner>({
    name: 'Owner',
    icon: 'account_circle',
    allValues: useMemo(
      () =>
        allAssetOwners.map((value) => ({
          value,
          match: [stringValueFromOwner(value)],
        })),
      [allAssetOwners],
    ),
    menuWidth: '300px',
    renderLabel: ({value}) => <UserDisplay email={stringValueFromOwner(value)} isFilter={true} />,
    getStringValue: (value) => stringValueFromOwner(value),
    state: memoizedState ?? emptyArray,
    onStateChanged: (values) => {
      setOwners?.(Array.from(values));
    },
  });
};

export function useAssetOwnersForAssets(
  assets: {
    definition?: {
      owners: AssetOwner[];
    } | null;
  }[],
): AssetOwner[] {
  return useMemo(
    () =>
      Array.from(
        new Set(
          assets
            .flatMap((a) => a.definition?.owners)
            .filter((o) => o)
            // Convert to JSON for deduping by Set
            .map((owner) => JSON.stringify(owner)),
        ),
        // Convert back to AssetOwner
      ).map((ownerJSON) => memoizedOwner(JSON.parse(ownerJSON))),
    [assets],
  );
}

const memoizedOwner = memoize(
  (owner: AssetOwner) => {
    return owner;
  },
  // Use a sequence unlikely to appear in the key/value to uniquely memoize them
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
