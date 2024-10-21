import {AssetOwner} from '../graphql/types';

export const assetOwnerAsString = (owner: AssetOwner) => {
  return owner.__typename === 'UserAssetOwner' ? owner.email : owner.team;
};
