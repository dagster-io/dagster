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
  buildUserAssetOwner,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {cache as mockedCache} from '../../util/idb-lru-cache';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {useAllAssets} from '../AssetsCatalogTable';
import {AssetCatalogTableQueryVersion} from '../types/AssetsCatalogTable.types';
import {AssetRecordsQuery, AssetRecordsQueryVariables} from '../types/useAllAssets.types';
import {ASSET_RECORDS_QUERY, AssetRecord} from '../useAllAssets';

jest.mock('../../util/idb-lru-cache', () => {
  const mockedCache = {
    has: jest.fn(),
    get: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
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
  });
});
