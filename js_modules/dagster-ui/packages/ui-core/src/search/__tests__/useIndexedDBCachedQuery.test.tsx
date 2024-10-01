import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, renderHook} from '@testing-library/react-hooks';
import {cache as _cache} from 'idb-lru-cache';
import {ReactNode, useMemo} from 'react';

import {useApolloClient} from '../../apollo-client';
import {ASSET_CATALOG_TABLE_QUERY} from '../../assets/AssetsCatalogTable';
import {AssetCatalogTableMockAssets} from '../../assets/__fixtures__/AssetTables.fixtures';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
} from '../../assets/types/AssetsCatalogTable.types';
import {buildAssetConnection} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {__resetForJest, useIndexedDBCachedQuery} from '../useIndexedDBCachedQuery';

const mockCache = _cache as any;

jest.useFakeTimers();

let mockShouldThrowError = false;

// Mock idb-lru-cache
jest.mock('idb-lru-cache', () => {
  const mockedCache = {
    has: jest.fn(),
    get: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
  };
  return {
    cache: jest.fn(() => {
      if (mockShouldThrowError) {
        throw new Error('Internal error opening backing store for indexedDB.open.');
      }
      return mockedCache;
    }),
  };
});

afterEach(() => {
  jest.resetModules();
});

jest.mock('@apollo/client', () => {
  const actual = jest.requireActual('@apollo/client');
  const query = jest.fn().mockReturnValue({
    data: {},
  });
  const client = {query};
  return {
    ...actual,
    useApolloClient: () => client,
  };
});

const mock = ({delay}: {delay: number} = {delay: 10}) =>
  buildQueryMock<AssetCatalogTableQuery, AssetCatalogTableQueryVariables>({
    query: ASSET_CATALOG_TABLE_QUERY,
    variableMatcher: () => true,
    data: {
      assetsOrError: buildAssetConnection({
        nodes: AssetCatalogTableMockAssets,
      }),
    },
    delay,
  });

describe('useIndexedDBCachedQuery', () => {
  const Wrapper = ({children, mocks}: {children: ReactNode; mocks: MockedResponse[]}) => (
    <MockedProvider mocks={mocks}>{children}</MockedProvider>
  );

  beforeEach(() => {
    jest.clearAllMocks();
  });

  [true, false].forEach((shouldThrowError) => {
    const throwingError = shouldThrowError;
    describe(
      // eslint-disable-next-line jest/valid-title
      throwingError ? 'with crashing indexeddb cache' : 'with working indexeddb cache',
      () => {
        beforeEach(() => {
          __resetForJest();
          mockShouldThrowError = throwingError;
        });

        it('should use cached data if available and version matches', async () => {
          if (!throwingError) {
            mockCache().has.mockResolvedValue(true);
            mockCache().get.mockResolvedValue({value: {data: 'test', version: 1}});
          }

          const {result, waitForNextUpdate} = renderHook(
            () =>
              useIndexedDBCachedQuery({
                key: 'testKey',
                query: ASSET_CATALOG_TABLE_QUERY,
                version: 1,
              }),
            {
              wrapper: ({children}: {children: ReactNode}) => (
                <Wrapper mocks={[mock({delay: Infinity})]}>{children}</Wrapper>
              ),
            },
          );
          expect(result.current.data).toBeUndefined();

          await act(async () => {
            await waitForNextUpdate();
          });

          expect(result.current.data).toBe(throwingError ? undefined : 'test');
        });

        it('should not return cached data if version does not match', async () => {
          if (!throwingError) {
            mockCache().has.mockResolvedValue(true);
            mockCache().get.mockResolvedValue({value: {data: 'test', version: 1}});
          }

          const {result} = renderHook(
            () =>
              useIndexedDBCachedQuery({
                key: 'testKey',
                query: ASSET_CATALOG_TABLE_QUERY,
                version: 2,
              }),
            {
              wrapper: ({children}: {children: ReactNode}) => (
                <Wrapper mocks={[]}>{children}</Wrapper>
              ),
            },
          );
          expect(result.current.data).toBeUndefined();
          jest.runAllTimers();
          expect(result.current.data).toBeUndefined();
        });

        it('Ensures that concurrent fetch requests consolidate correctly, not triggering multiple network requests for the same key', async () => {
          if (!throwingError) {
            mockCache().has.mockResolvedValue(false);
          }
          const mock1 = mock();
          const mock2 = mock();
          let result1;
          let result2;
          renderHook(
            () => {
              result1 = useIndexedDBCachedQuery({
                key: 'testKey',
                query: ASSET_CATALOG_TABLE_QUERY,
                version: 2,
              });
              const {fetch} = result1;
              useMemo(() => fetch(), [fetch]);
              result2 = useIndexedDBCachedQuery({
                key: 'testKey',
                query: ASSET_CATALOG_TABLE_QUERY,
                version: 2,
              });
              const {fetch: fetch2} = result2;
              useMemo(() => fetch2(), [fetch2]);
              return result2;
            },
            {
              wrapper: ({children}: {children: ReactNode}) => (
                <Wrapper mocks={[mock1, mock2]}>{children}</Wrapper>
              ),
            },
          );
          expect(useApolloClient().query).toHaveBeenCalledTimes(1);
          expect(result1!.data).toEqual(result2!.data);
          expect(result1!.loading).toEqual(result2!.loading);
        });
      },
    );
  });
});
