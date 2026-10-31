import {MockedProvider} from '@apollo/client/testing';
import {renderHook, waitFor} from '@testing-library/react';

import {
  buildAssetKey,
  buildAssetNode,
  buildAssetRecord,
  buildAssetRecordConnection,
  buildDefinitionTag,
  buildRepository,
  buildRepositoryLocation,
  buildTeamAssetOwner,
  buildTimeWindowFreshnessPolicy,
  buildUserAssetOwner,
  buildWorkspaceLocationEntry,
} from '../../graphql/builders';
import {buildQueryMock, getMockResultFn} from '../../testing/mocking';
import {cache as mockedCache} from '../../util/idb-lru-cache';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {useAllAssets} from '../AssetsCatalogTable';
import {AssetCatalogTableQueryVersion} from '../types/AssetsCatalogTable.types';
import {AssetRecordsQuery, AssetRecordsQueryVariables} from '../types/useAllAssets.types';
import {ASSET_RECORDS_QUERY, AssetRecord} from '../useAllAssets';

interface MockCacheInstance {
  has: jest.Mock;
  get: jest.Mock;
  set: jest.Mock;
  delete: jest.Mock;
  constructorArgs: unknown;
}

jest.mock('../../util/idb-lru-cache', () => {
  const mockedCacheInstance = {
    has: jest.fn(),
    get: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
    constructorArgs: {},
  };

  return {
    cache: (...args: unknown[]) => {
      mockedCacheInstance.constructorArgs = args;
      return mockedCacheInstance;
    },
  };
});

const getMockCacheInstance = (): MockCacheInstance =>
  (mockedCache as unknown as (...args: unknown[]) => MockCacheInstance)();

const createMock = ({
  nodes,
  returnedCursor,
  cursor,
  limit = 2,
}: {
  limit?: number;
  returnedCursor: string | null;
  cursor?: string;
  nodes: AssetRecord[];
}) =>
  buildQueryMock<AssetRecordsQuery, AssetRecordsQueryVariables>({
    query: ASSET_RECORDS_QUERY,
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
        return (
          <MockedProvider mocks={[mock, mock2, mock3, ...buildWorkspaceMocks([], {delay: 10})]}>
            <WorkspaceProvider>{props.children}</WorkspaceProvider>
          </MockedProvider>
        );
      },
    });

    expect(result.current.loading).toBe(true);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.assets?.length).toBe(5);
  });

  it('Loads from Indexeddb cache and also requests latest data', async () => {
    getMockCacheInstance().has.mockResolvedValue(true);
    getMockCacheInstance().get.mockResolvedValueOnce({
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

  it('does not request asset records until skip is turned off', async () => {
    const mock = createMock({nodes: [buildAssetRecord({id: 'asset-id-1'})], returnedCursor: null});
    const mockResult = getMockResultFn(mock);

    const {result, rerender} = renderHook(
      ({skip}: {skip: boolean}) => useAllAssets({batchLimit: 2, skip}),
      {
        initialProps: {skip: true},
        wrapper(props) {
          return <MockedProvider mocks={[mock]}>{props.children}</MockedProvider>;
        },
      },
    );

    // Wait past the mock's delay so a request, if made, would have resolved.
    await new Promise((resolve) => setTimeout(resolve, 250));
    expect(mockResult).not.toHaveBeenCalled();
    expect(result.current.assets).toEqual([]);

    rerender({skip: false});

    await waitFor(() => {
      expect(result.current.assets?.length).toBe(1);
    });
    expect(mockResult).toHaveBeenCalledTimes(1);
  });

  it('resumes fetching when a subscriber returns after polling stopped', async () => {
    const firstMock = createMock({
      limit: 10,
      nodes: [buildAssetRecord({id: 'asset-id-1'})],
      returnedCursor: null,
    });
    const secondMock = createMock({
      limit: 10,
      nodes: [buildAssetRecord({id: 'asset-id-1'}), buildAssetRecord({id: 'asset-id-2'})],
      returnedCursor: null,
    });
    const firstResult = getMockResultFn(firstMock);
    const secondResult = getMockResultFn(secondMock);

    const {result, rerender} = renderHook(
      ({skip}: {skip: boolean}) => useAllAssets({batchLimit: 10, skip}),
      {
        initialProps: {skip: false},
        wrapper(props) {
          // Bypass the Apollo cache so the restarted fetch reaches the mocks.
          return (
            <MockedProvider
              defaultOptions={{query: {fetchPolicy: 'network-only'}}}
              mocks={[firstMock, secondMock]}
            >
              {props.children}
            </MockedProvider>
          );
        },
      },
    );

    // Unsubscribe while the first fetch is in flight, so it completes with no subscribers and
    // schedules no further poll.
    rerender({skip: true});
    await new Promise((resolve) => setTimeout(resolve, 250));
    expect(firstResult).toHaveBeenCalledTimes(1);

    rerender({skip: false});

    await waitFor(() => {
      expect(result.current.assets?.length).toBe(2);
    });
    expect(secondResult).toHaveBeenCalledTimes(1);
  });

  it('dedupes SDAs that are defined in multiple locations and combines their definitions', async () => {
    const assetNode1 = buildAssetNode({
      assetKey: buildAssetKey({path: ['asset_key']}),
      kinds: ['dbt'],
      groupName: 'default',
      owners: [
        buildTeamAssetOwner({team: 'my-team'}),
        buildUserAssetOwner({email: 'fake-email@gmail.com'}),
      ],
      tags: [buildDefinitionTag({key: 'tag', value: 'value'})],
      repository: buildRepository({
        name: 'repoName',
        location: buildRepositoryLocation({name: 'locationName'}),
      }),
      isMaterializable: true,
      isObservable: false,
      internalFreshnessPolicy: null,
    });

    const assetNode2 = buildAssetNode({
      assetKey: buildAssetKey({path: ['asset_key']}), // Same asset key
      kinds: ['python'],
      groupName: 'default',
      owners: [buildTeamAssetOwner({team: 'another-team'})],
      tags: [buildDefinitionTag({key: 'tag2', value: 'value2'})],
      repository: buildRepository({
        name: 'anotherRepoName',
        location: buildRepositoryLocation({name: 'anotherLocationName'}),
      }),
      isMaterializable: false,
      isObservable: true,
      internalFreshnessPolicy: buildTimeWindowFreshnessPolicy({failWindowSeconds: 3600}),
    });

    const workspaceWithDuplicateAssets = buildWorkspaceMocks([
      buildWorkspaceLocationEntry({
        id: 'location1',
        name: 'location1',
        locationOrLoadError: buildRepositoryLocation({
          id: 'location1',
          name: 'location1',
          repositories: [
            buildRepository({
              id: 'repo1',
              name: 'repoName',
              assetNodes: [assetNode1],
            }),
          ],
        }),
      }),
      buildWorkspaceLocationEntry({
        id: 'location2',
        name: 'location2',
        locationOrLoadError: buildRepositoryLocation({
          id: 'location2',
          name: 'location2',
          repositories: [
            buildRepository({
              id: 'repo2',
              name: 'anotherRepoName',
              assetNodes: [assetNode2],
            }),
          ],
        }),
      }),
    ]);

    // Mock the ASSET_RECORDS_QUERY to return empty data
    const assetRecordsMock = createMock({
      nodes: [],
      returnedCursor: null,
      limit: 1000,
    });

    const {result} = renderHook(() => useAllAssets({}), {
      wrapper(props) {
        return (
          <MockedProvider mocks={[...workspaceWithDuplicateAssets, assetRecordsMock]}>
            <WorkspaceProvider>{props.children}</WorkspaceProvider>
          </MockedProvider>
        );
      },
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Should have exactly 1 asset (deduplicated)
    expect(result.current.assets?.length).toBe(1);

    const asset = result.current.assets?.[0];
    expect(asset).toBeDefined();
    expect(asset?.key.path).toEqual(['asset_key']);

    // Should prefer materializable asset (assetNode1) as the base
    expect(asset?.definition?.isMaterializable).toBe(true);

    // Should merge boolean fields (OR of both values)
    expect(asset?.definition?.isObservable).toBe(true);

    // Should merge array fields (union of all values)
    expect(asset?.definition?.kinds).toEqual(expect.arrayContaining(['dbt', 'python']));
    expect(asset?.definition?.owners).toEqual(
      expect.arrayContaining([
        expect.objectContaining({team: 'my-team'}),
        expect.objectContaining({email: 'fake-email@gmail.com'}),
        expect.objectContaining({team: 'another-team'}),
      ]),
    );
    expect(asset?.definition?.tags).toEqual(
      expect.arrayContaining([
        expect.objectContaining({key: 'tag', value: 'value'}),
        expect.objectContaining({key: 'tag2', value: 'value2'}),
      ]),
    );

    // A freshness policy declared on only the non-representative definition still surfaces
    expect(asset?.definition?.internalFreshnessPolicy).toEqual(
      expect.objectContaining({failWindowSeconds: 3600}),
    );
  });
});
