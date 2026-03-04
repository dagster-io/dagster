import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {renderHook, waitFor} from '@testing-library/react';
import {ReactNode} from 'react';

import {buildAssetNode} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {
  AssetsPermissionsQuery,
  AssetsPermissionsQueryVariables,
} from '../types/useAssetPermissions.types';
import {ASSETS_PERMISSIONS_QUERY, useAssetPermissions} from '../useAssetPermissions';

// Mock the usePermissionsForLocation hook
jest.mock('../../app/Permissions', () => ({
  usePermissionsForLocation: () => ({
    permissions: {
      canLaunchPipelineExecution: true,
      canWipeAssets: true,
      canReportRunlessAssetEvents: true,
    },
    loading: false,
  }),
}));

const createMock = (
  assetKeys: Array<{path: string[]}>,
  permissions: Array<{
    hasMaterializePermission: boolean;
    hasWipePermission: boolean;
    hasReportRunlessAssetEventPermission: boolean;
  }>,
): MockedResponse<AssetsPermissionsQuery> => {
  return buildQueryMock<AssetsPermissionsQuery, AssetsPermissionsQueryVariables>({
    query: ASSETS_PERMISSIONS_QUERY,
    variables: {
      assetKeys: assetKeys.map((key) => ({path: key.path})),
    },
    data: {
      assetNodes: permissions.map((perm, i) =>
        buildAssetNode({
          id: `asset-${i}`,
          hasMaterializePermission: perm.hasMaterializePermission,
          hasWipePermission: perm.hasWipePermission,
          hasReportRunlessAssetEventPermission: perm.hasReportRunlessAssetEventPermission,
        }),
      ),
    },
  });
};

const wrapper = (mocks: MockedResponse[]) => {
  return ({children}: {children: ReactNode}) => (
    <MockedProvider mocks={mocks}>{children}</MockedProvider>
  );
};

describe('useAssetPermissions', () => {
  it('returns true for all permissions when all assets allow them', async () => {
    const assetKeys = [{path: ['asset1']}, {path: ['asset2']}, {path: ['asset3']}];
    const mock = createMock(assetKeys, [
      {
        hasMaterializePermission: true,
        hasWipePermission: true,
        hasReportRunlessAssetEventPermission: true,
      },
      {
        hasMaterializePermission: true,
        hasWipePermission: true,
        hasReportRunlessAssetEventPermission: true,
      },
      {
        hasMaterializePermission: true,
        hasWipePermission: true,
        hasReportRunlessAssetEventPermission: true,
      },
    ]);

    const {result} = renderHook(() => useAssetPermissions(assetKeys, 'test-location'), {
      wrapper: wrapper([mock]),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.hasMaterializePermission).toBe(true);
    expect(result.current.hasWipePermission).toBe(true);
    expect(result.current.hasReportRunlessAssetEventPermission).toBe(true);
  });

  it('returns false for permissions when any asset denies them', async () => {
    const assetKeys = [{path: ['asset1']}, {path: ['asset2']}, {path: ['asset3']}];
    const mock = createMock(assetKeys, [
      {
        hasMaterializePermission: true,
        hasWipePermission: true,
        hasReportRunlessAssetEventPermission: true,
      },
      {
        hasMaterializePermission: false, // This one denies materialize
        hasWipePermission: true,
        hasReportRunlessAssetEventPermission: true,
      },
      {
        hasMaterializePermission: true,
        hasWipePermission: true,
        hasReportRunlessAssetEventPermission: true,
      },
    ]);

    const {result} = renderHook(() => useAssetPermissions(assetKeys, 'test-location'), {
      wrapper: wrapper([mock]),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.hasMaterializePermission).toBe(false); // Should be false
    expect(result.current.hasWipePermission).toBe(true); // Should still be true
    expect(result.current.hasReportRunlessAssetEventPermission).toBe(true);
  });

  it('returns false when multiple permissions are denied across different assets', async () => {
    const assetKeys = [{path: ['asset1']}, {path: ['asset2']}, {path: ['asset3']}];
    const mock = createMock(assetKeys, [
      {
        hasMaterializePermission: true,
        hasWipePermission: false, // First asset denies wipe
        hasReportRunlessAssetEventPermission: true,
      },
      {
        hasMaterializePermission: true,
        hasWipePermission: true,
        hasReportRunlessAssetEventPermission: false, // Second asset denies runless event
      },
      {
        hasMaterializePermission: false, // Third asset denies materialize
        hasWipePermission: true,
        hasReportRunlessAssetEventPermission: true,
      },
    ]);

    const {result} = renderHook(() => useAssetPermissions(assetKeys, 'test-location'), {
      wrapper: wrapper([mock]),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.hasMaterializePermission).toBe(false);
    expect(result.current.hasWipePermission).toBe(false);
    expect(result.current.hasReportRunlessAssetEventPermission).toBe(false);
  });

  it('returns location permissions when no asset keys provided', async () => {
    const {result} = renderHook(() => useAssetPermissions([], 'test-location'), {
      wrapper: wrapper([]),
    });

    // Should return immediately with location permissions since query is skipped
    expect(result.current.hasMaterializePermission).toBe(true);
    expect(result.current.hasWipePermission).toBe(true);
    expect(result.current.hasReportRunlessAssetEventPermission).toBe(true);
  });

  it('handles single asset key', async () => {
    const assetKeys = [{path: ['single-asset']}];
    const mock = createMock(assetKeys, [
      {
        hasMaterializePermission: true,
        hasWipePermission: false,
        hasReportRunlessAssetEventPermission: true,
      },
    ]);

    const {result} = renderHook(() => useAssetPermissions(assetKeys, 'test-location'), {
      wrapper: wrapper([mock]),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.hasMaterializePermission).toBe(true);
    expect(result.current.hasWipePermission).toBe(false);
    expect(result.current.hasReportRunlessAssetEventPermission).toBe(true);
  });
});
