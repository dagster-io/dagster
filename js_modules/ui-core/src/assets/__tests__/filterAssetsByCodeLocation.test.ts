import {filterAssetsByCodeLocation} from '../filterAssetsByCodeLocation';

const assetIn = (location: string) => ({definition: {repository: {location: {name: location}}}});

describe('filterAssetsByCodeLocation', () => {
  const sales = assetIn('sales');
  const finance = assetIn('finance');
  const external = {definition: null};

  it('returns all assets when no code location is selected', () => {
    const assets = [sales, finance, external];
    expect(filterAssetsByCodeLocation(assets, null)).toBe(assets);
  });

  it('keeps only assets defined in the selected code location', () => {
    expect(filterAssetsByCodeLocation([sales, finance, external], 'sales')).toEqual([sales]);
  });
});
