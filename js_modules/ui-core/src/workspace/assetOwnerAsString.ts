// eslint-disable-next-line no-restricted-imports
import {AssetOwner} from '../graphql/types-do-not-use';

export const assetOwnerAsString = (owner: AssetOwner) => {
  return owner.__typename === 'UserAssetOwner' ? owner.email : owner.team;
};
