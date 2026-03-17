type AssetOwner =
  | {__typename: 'TeamAssetOwner'; team: string}
  | {__typename: 'UserAssetOwner'; email: string};

export const assetOwnerAsString = (owner: AssetOwner) => {
  return owner.__typename === 'UserAssetOwner' ? owner.email : owner.team;
};
