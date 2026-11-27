import {renderHook} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {AssetHealthFragment} from '../../../asset-data/types/AssetHealthDataProvider.types';
import {buildAsset, buildAssetKey, buildAssetNode} from '../../../graphql/builders';
import {AssetTableFragment} from '../../types/AssetTableFragment.types';
import {useAssetCatalogGroupAndSortBy} from '../useAssetCatalogGroupAndSortBy';

const asset = (path: string[]): AssetTableFragment =>
  buildAsset({key: buildAssetKey({path}), definition: buildAssetNode({groupName: 'g'})});

const health = (
  path: string[],
  latestMaterializationTimestamp: number | null,
): AssetHealthFragment => buildAsset({key: buildAssetKey({path}), latestMaterializationTimestamp});

const assetsByAssetKey = new Map(
  [['b'], ['a', 'z'], ['c']].map((path) => [path.join('/'), asset(path)]),
);

const liveDataByNode = {
  b: health(['b'], 200),
  'a/z': health(['a', 'z'], null),
  c: health(['c'], 300),
};

function renderSortHook(search: string) {
  return renderHook(
    ({liveDataByNode}) => useAssetCatalogGroupAndSortBy({liveDataByNode, assetsByAssetKey}),
    {
      initialProps: {liveDataByNode},
      wrapper: ({children}) => (
        <MemoryRouter initialEntries={[`/catalog?${search}`]}>{children}</MemoryRouter>
      ),
    },
  );
}

const sortedPaths = (result: ReturnType<typeof renderSortHook>['result']) =>
  result.current.groupedAndSorted['g']?.assets.map((a) => a.key.path.join('/'));

describe('useAssetCatalogGroupAndSortBy', () => {
  it('sorts by asset key', () => {
    expect(sortedPaths(renderSortHook('groupBy=group&sortBy=key_asc').result)).toEqual([
      'a/z',
      'b',
      'c',
    ]);
    expect(sortedPaths(renderSortHook('groupBy=group&sortBy=key_desc').result)).toEqual([
      'c',
      'b',
      'a/z',
    ]);
  });

  it('sorts by materialization time using health data, unmaterialized last', () => {
    expect(sortedPaths(renderSortHook('groupBy=group&sortBy=materialization_asc').result)).toEqual([
      'c',
      'b',
      'a/z',
    ]);
    expect(sortedPaths(renderSortHook('groupBy=group&sortBy=materialization_desc').result)).toEqual(
      ['a/z', 'b', 'c'],
    );
  });

  it('does not re-sort by key when only health data changes', () => {
    const {result, rerender} = renderSortHook('groupBy=group&sortBy=key_asc');
    const before = result.current.groupedAndSorted;
    rerender({liveDataByNode: {...liveDataByNode}});
    expect(result.current.groupedAndSorted).toBe(before);
  });

  it('re-sorts by materialization when health data changes', () => {
    const {result, rerender} = renderSortHook('groupBy=group&sortBy=materialization_asc');
    rerender({liveDataByNode: {...liveDataByNode, 'a/z': health(['a', 'z'], 400)}});
    expect(sortedPaths(result)).toEqual(['a/z', 'c', 'b']);
  });
});
