import {
  globalAssetGraphPathToString,
  globalAssetGraphPathForAssetsAndDescendants,
} from '../globalAssetGraphPathToString';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

describe('Global Graph URLs', () => {
  describe('globalAssetGraphPathToString', () => {
    it('should return a valid path given a selection and query', async () => {
      const url = globalAssetGraphPathToString({
        opNames: ['foo_bar'],
        opsQuery: `foo*, bar, foo_bar++`,
      });
      expect(url).toEqual(`/asset-groups~foo*%2C%20bar%2C%20foo_bar%2B%2B/foo_bar`);
    });
  });

  describe('globalAssetGraphPathForAssetsAndDescendants', () => {
    it('should return a valid path for a single asset', async () => {
      const url = globalAssetGraphPathForAssetsAndDescendants([{path: ['asset_0']}]);
      expect(url).toEqual(`/asset-groups~asset_0*/asset_0`);
    });

    it('should avoid exceeding a 32k character URL', async () => {
      const keysLarge = new Array(900).fill(0).map((_, idx) => ({path: [`asset_${idx}`]}));
      const urlLarge = globalAssetGraphPathForAssetsAndDescendants(keysLarge);
      expect(urlLarge.length).toEqual(24986);

      const keysHuge = new Array(1500).fill(0).map((_, idx) => ({path: [`asset_${idx}`]}));
      const urlHuge = globalAssetGraphPathForAssetsAndDescendants(keysHuge);
      expect(urlHuge.length).toEqual(24399); // smaller because the selection is not passed
    });
  });
});
