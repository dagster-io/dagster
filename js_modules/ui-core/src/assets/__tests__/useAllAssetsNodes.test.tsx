import {renderHook} from '@testing-library/react';
import {useContext} from 'react';

import {buildAssetKey} from '../../graphql/types';
import {WorkspaceContext} from '../../workspace/WorkspaceContext/WorkspaceContext';

// Mock WorkspaceContext
const mockWorkspaceContext = {
  assetEntries: {},
  loadingAssets: false,
};

jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useContext: jest.fn(),
}));

const mockUseContext = useContext as jest.MockedFunction<typeof useContext>;

describe('useAllAssetsNodes integration tests', () => {
  let useAllAssetsNodes: any;

  beforeAll(() => {
    // Import after mocks are set up
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const module = require('../useAllAssets');
    useAllAssetsNodes = module.useAllAssetsNodes;
  });

  beforeEach(() => {
    mockUseContext.mockImplementation((context: any) => {
      if (context === WorkspaceContext) {
        return mockWorkspaceContext;
      }
      return jest.requireActual('react').useContext(context);
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('allAssetKeys functionality', () => {
    it('should return allAssetKeys as a Set of tokenized asset keys', () => {
      // Mock the asset entries to return specific assets
      const mockAssetEntries = {
        'test-location': {
          workspaceLocationEntryOrError: {
            __typename: 'WorkspaceLocationEntry' as const,
            locationOrLoadError: {
              __typename: 'RepositoryLocation' as const,
              repositories: [
                {
                  assetNodes: [
                    {
                      id: 'asset1-id',
                      assetKey: buildAssetKey({path: ['asset1']}),
                    },
                    {
                      id: 'asset2-id',
                      assetKey: buildAssetKey({path: ['namespace', 'asset2']}),
                    },
                    {
                      id: 'asset3-id',
                      assetKey: buildAssetKey({path: ['complex', 'nested', 'asset3']}),
                    },
                  ],
                },
              ],
            },
          },
        },
      };

      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: mockAssetEntries,
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      expect(result.current.allAssetKeys).toBeInstanceOf(Set);
      expect(result.current.allAssetKeys.size).toBe(3);

      // Check that the Set contains tokenized versions of the asset keys
      expect(result.current.allAssetKeys.has('asset1')).toBe(true);
      expect(result.current.allAssetKeys.has('namespace/asset2')).toBe(true);
      expect(result.current.allAssetKeys.has('complex/nested/asset3')).toBe(true);
    });

    it('should return empty Set when no asset nodes exist', () => {
      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: {},
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      expect(result.current.allAssetKeys).toBeInstanceOf(Set);
      expect(result.current.allAssetKeys.size).toBe(0);
    });

    it('should maintain backward compatibility with assets property', () => {
      const mockAssetEntries = {
        'test-location': {
          workspaceLocationEntryOrError: {
            __typename: 'WorkspaceLocationEntry' as const,
            locationOrLoadError: {
              __typename: 'RepositoryLocation' as const,
              repositories: [
                {
                  assetNodes: [
                    {
                      id: 'asset1-id',
                      assetKey: buildAssetKey({path: ['asset1']}),
                    },
                    {
                      id: 'asset2-id',
                      assetKey: buildAssetKey({path: ['asset2']}),
                    },
                  ],
                },
              ],
            },
          },
        },
      };

      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: mockAssetEntries,
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      // Existing assets property should still be available
      expect(result.current.assets).toBeDefined();
      expect(Array.isArray(result.current.assets)).toBe(true);
      expect(result.current.assets.length).toBe(2);
    });

    it('should maintain loading property', () => {
      // Test with loading = true
      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: {},
            loadingAssets: true,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      expect(result.current.loading).toBe(true);

      // Test with loading = false
      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: {},
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result: result2} = renderHook(() => useAllAssetsNodes());

      expect(result2.current.loading).toBe(false);
    });

    it('should handle complex nested asset key paths', () => {
      const mockAssetEntries = {
        'test-location': {
          workspaceLocationEntryOrError: {
            __typename: 'WorkspaceLocationEntry' as const,
            locationOrLoadError: {
              __typename: 'RepositoryLocation' as const,
              repositories: [
                {
                  assetNodes: [
                    {
                      id: 'complex-asset-id',
                      assetKey: buildAssetKey({
                        path: ['very', 'deeply', 'nested', 'namespace', 'asset_name'],
                      }),
                    },
                  ],
                },
              ],
            },
          },
        },
      };

      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: mockAssetEntries,
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      expect(result.current.allAssetKeys.size).toBe(1);
      expect(result.current.allAssetKeys.has('very/deeply/nested/namespace/asset_name')).toBe(true);
    });

    it('should handle special characters in asset keys', () => {
      const mockAssetEntries = {
        'test-location': {
          workspaceLocationEntryOrError: {
            __typename: 'WorkspaceLocationEntry' as const,
            locationOrLoadError: {
              __typename: 'RepositoryLocation' as const,
              repositories: [
                {
                  assetNodes: [
                    {
                      id: 'special-chars-id',
                      assetKey: buildAssetKey({
                        path: ['asset-with-dashes', 'asset_with_underscores', 'asset.with.dots'],
                      }),
                    },
                  ],
                },
              ],
            },
          },
        },
      };

      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: mockAssetEntries,
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      expect(result.current.allAssetKeys.size).toBe(1);
      expect(
        result.current.allAssetKeys.has('asset-with-dashes/asset_with_underscores/asset.with.dots'),
      ).toBe(true);
    });

    it('should return correct structure with all three properties', () => {
      const mockAssetEntries = {
        'test-location': {
          workspaceLocationEntryOrError: {
            __typename: 'WorkspaceLocationEntry' as const,
            locationOrLoadError: {
              __typename: 'RepositoryLocation' as const,
              repositories: [
                {
                  assetNodes: [
                    {
                      id: 'test-asset-id',
                      assetKey: buildAssetKey({path: ['test']}),
                    },
                  ],
                },
              ],
            },
          },
        },
      };

      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: mockAssetEntries,
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      // Check that all expected properties are present
      expect(result.current).toHaveProperty('assets');
      expect(result.current).toHaveProperty('allAssetKeys');
      expect(result.current).toHaveProperty('loading');

      // Check types
      expect(Array.isArray(result.current.assets)).toBe(true);
      expect(result.current.allAssetKeys).toBeInstanceOf(Set);
      expect(typeof result.current.loading).toBe('boolean');

      // Check the new allAssetKeys property specifically
      expect(result.current.allAssetKeys.size).toBe(1);
      expect(result.current.allAssetKeys.has('test')).toBe(true);
    });

    it('should handle multiple repositories in same location', () => {
      const mockAssetEntries = {
        'test-location': {
          workspaceLocationEntryOrError: {
            __typename: 'WorkspaceLocationEntry' as const,
            locationOrLoadError: {
              __typename: 'RepositoryLocation' as const,
              repositories: [
                {
                  assetNodes: [
                    {
                      id: 'repo1-asset-id',
                      assetKey: buildAssetKey({path: ['repo1_asset']}),
                    },
                  ],
                },
                {
                  assetNodes: [
                    {
                      id: 'repo2-asset-id',
                      assetKey: buildAssetKey({path: ['repo2_asset']}),
                    },
                  ],
                },
              ],
            },
          },
        },
      };

      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: mockAssetEntries,
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      expect(result.current.allAssetKeys.size).toBe(2);
      expect(result.current.allAssetKeys.has('repo1_asset')).toBe(true);
      expect(result.current.allAssetKeys.has('repo2_asset')).toBe(true);
    });

    it('should handle multiple locations', () => {
      const mockAssetEntries = {
        location1: {
          workspaceLocationEntryOrError: {
            __typename: 'WorkspaceLocationEntry' as const,
            locationOrLoadError: {
              __typename: 'RepositoryLocation' as const,
              repositories: [
                {
                  assetNodes: [
                    {
                      id: 'loc1-asset-id',
                      assetKey: buildAssetKey({path: ['location1_asset']}),
                    },
                  ],
                },
              ],
            },
          },
        },
        location2: {
          workspaceLocationEntryOrError: {
            __typename: 'WorkspaceLocationEntry' as const,
            locationOrLoadError: {
              __typename: 'RepositoryLocation' as const,
              repositories: [
                {
                  assetNodes: [
                    {
                      id: 'loc2-asset-id',
                      assetKey: buildAssetKey({path: ['location2_asset']}),
                    },
                  ],
                },
              ],
            },
          },
        },
      };

      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: mockAssetEntries,
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      expect(result.current.allAssetKeys.size).toBe(2);
      expect(result.current.allAssetKeys.has('location1_asset')).toBe(true);
      expect(result.current.allAssetKeys.has('location2_asset')).toBe(true);
    });

    it('should handle error states in workspace entries', () => {
      const mockAssetEntries = {
        'error-location': {
          workspaceLocationEntryOrError: {
            __typename: 'PythonError' as const,
            message: 'Location failed to load',
          },
        },
        'good-location': {
          workspaceLocationEntryOrError: {
            __typename: 'WorkspaceLocationEntry' as const,
            locationOrLoadError: {
              __typename: 'RepositoryLocation' as const,
              repositories: [
                {
                  assetNodes: [
                    {
                      id: 'good-asset-id',
                      assetKey: buildAssetKey({path: ['good_asset']}),
                    },
                  ],
                },
              ],
            },
          },
        },
      };

      mockUseContext.mockImplementation((context: any) => {
        if (context === WorkspaceContext) {
          return {
            assetEntries: mockAssetEntries,
            loadingAssets: false,
          };
        }
        return jest.requireActual('react').useContext(context);
      });

      const {result} = renderHook(() => useAllAssetsNodes());

      // Should only have the asset from the good location
      expect(result.current.allAssetKeys.size).toBe(1);
      expect(result.current.allAssetKeys.has('good_asset')).toBe(true);
    });
  });
});
