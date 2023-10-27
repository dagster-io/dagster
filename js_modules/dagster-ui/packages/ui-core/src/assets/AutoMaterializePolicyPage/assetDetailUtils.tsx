export enum AssetDetailType {
  Updated,
  WillUpdate,
}

export const detailTypeToLabel = (detailType: AssetDetailType) => {
  switch (detailType) {
    case AssetDetailType.Updated:
      return 'Updated';
    case AssetDetailType.WillUpdate:
      return 'Will update';
  }
};
