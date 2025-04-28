import {MockedProvider} from '@apollo/client/testing';
import {renderHook, waitFor} from '@testing-library/react';

import {buildAssetRecord, buildAssetRecordConnection} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {cache as mockedCache} from '../../util/idb-lru-cache';
import {useAllAssets} from '../AssetsCatalogTable';
import {AssetCatalogTableQueryVersion} from '../types/AssetsCatalogTable.types';
import {AssetsStateQuery, AssetsStateQueryVariables} from '../types/useAllAssets.types';
import {ASSETS_STATE_QUERY, AssetState} from '../useAllAssets';

jest.mock('../../util/idb-lru-cache', () => {
  const mockedCache = {
    has: jest.fn(),
    get: jest.fn(),
    set: jest.fn(),
    constructorArgs: {},
  };

  return {
    cache: (...args: any[]) => {
      mockedCache.constructorArgs = args;
      return mockedCache;
    },
  };
});

const createMock = ({
  nodes,
  returnedCursor,
  cursor,
  limit = 2,
}: {
  limit?: number;
  returnedCursor: string | null;
  cursor?: string;
  nodes: AssetState[];
}) =>
  buildQueryMock<AssetsStateQuery, AssetsStateQueryVariables>({
    query: ASSETS_STATE_QUERY,
    variables: {
      limit,
      cursor,
    },
    data: {
      assetRecordsOrError: buildAssetRecordConnection({
        assets: nodes,
        cursor: returnedCursor,
      }),
    },
    delay: 100,
  });

describe('useAllAssets', () => {
  it('Paginates correctly', async () => {
    const mock = createMock({
      nodes: [buildAssetRecord({id: 'asset-id-1'}), buildAssetRecord({id: 'asset-id-2'})],
      returnedCursor: 'asset-key-2',
    });
    const mock2 = createMock({
      cursor: 'asset-key-2',
      nodes: [buildAssetRecord({id: 'asset-id-3'}), buildAssetRecord({id: 'asset-id-4'})],
      returnedCursor: 'asset-key-4',
    });
    const mock3 = createMock({
      cursor: 'asset-key-4',
      nodes: [buildAssetRecord({id: 'asset-id-5'})],
      returnedCursor: null,
    });

    const {result} = renderHook(() => useAllAssets({batchLimit: 2}), {
      wrapper(props) {
        return <MockedProvider mocks={[mock, mock2, mock3]}>{props.children}</MockedProvider>;
      },
    });

    expect(result.current.loading).toBe(true);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.assets?.length).toBe(5);
  });

  it('Loads from Indexeddb cache and also requests latest data', async () => {
    (mockedCache as any)().has.mockResolvedValue(true);
    (mockedCache as any)().get.mockResolvedValueOnce({
      value: {
        data: [buildAssetRecord()],
        version: AssetCatalogTableQueryVersion,
      },
    });
    const mock = createMock({
      nodes: [buildAssetRecord({id: 'asset-id-1'}), buildAssetRecord({id: 'asset-id-2'})],
      returnedCursor: 'asset-key-2',
    });
    const mock2 = createMock({
      cursor: 'asset-key-2',
      nodes: [buildAssetRecord({id: 'asset-id-3'}), buildAssetRecord({id: 'asset-id-4'})],
      returnedCursor: 'asset-key-4',
    });
    const mock3 = createMock({
      cursor: 'asset-key-4',
      nodes: [buildAssetRecord({id: 'asset-id-5'})],
      returnedCursor: null,
    });

    const {result} = renderHook(() => useAllAssets({batchLimit: 2}), {
      wrapper(props) {
        return <MockedProvider mocks={[mock, mock2, mock3]}>{props.children}</MockedProvider>;
      },
    });

    await waitFor(() => {
      expect(result.current.assets?.length).toBe(5);
    });
  });
});
