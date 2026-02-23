import {MockedProvider} from '@apollo/client/testing';
import {useAssetGraphSupplementaryData} from '@shared/asset-graph/useAssetGraphSupplementaryData';
import {renderHook, waitFor} from '@testing-library/react';
import React from 'react';

import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {parseExpression} from '../../asset-selection/AssetSelectionSupplementaryDataVisitor';
import {useAllAssets} from '../../assets/useAllAssets';
import {AssetHealthStatus, buildAsset, buildAssetHealth, buildAssetKey} from '../../graphql/types';
import {WorkspaceAssetFragment} from '../../workspace/WorkspaceContext/types/WorkspaceQueries.types';

// Mock the dependencies
jest.mock('../Utils', () => ({
  tokenForAssetKey: jest.fn((key) => JSON.stringify(key.path)),
}));

jest.mock('../../asset-data/AssetHealthDataProvider', () => ({
  useAssetsHealthData: jest.fn(),
}));

jest.mock('../../assets/useAllAssets', () => ({
  useAllAssets: jest.fn(),
}));

jest.mock('../../asset-selection/AssetSelectionSupplementaryDataVisitor', () => ({
  parseExpression: jest.fn(),
}));

jest.mock('../../hooks/useStableReferenceByHash', () => ({
  useStableReferenceByHash: jest.fn((data) => data),
}));

const mockUseAssetsHealthData = useAssetsHealthData as jest.MockedFunction<
  typeof useAssetsHealthData
>;
const mockUseAllAssets = useAllAssets as jest.MockedFunction<typeof useAllAssets>;
const mockParseExpression = parseExpression as jest.MockedFunction<typeof parseExpression>;

// Test wrapper component
function TestWrapper({children}: {children: React.ReactNode}) {
  return <MockedProvider mocks={[]}>{children}</MockedProvider>;
}

describe('useAssetGraphSupplementaryData', () => {
  const mockAssetKey1 = buildAssetKey({path: ['asset1']});
  const mockAssetKey2 = buildAssetKey({path: ['asset2']});

  const mockNodes: WorkspaceAssetFragment[] = [
    {
      assetKey: mockAssetKey1,
      // Add other required properties for WorkspaceAssetFragment
    } as WorkspaceAssetFragment,
    {
      assetKey: mockAssetKey2,
    } as WorkspaceAssetFragment,
  ];

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockParseExpression.mockReturnValue([{field: 'status', value: 'HEALTHY'} as any]);
    mockUseAllAssets.mockReturnValue({
      assetsByAssetKey: new Map([
        [
          JSON.stringify(['asset1']),
          {
            definition: {
              internalFreshnessPolicy: null,
              hasAssetChecks: false,
            },
          },
        ],
        [
          JSON.stringify(['asset2']),
          {
            definition: {
              internalFreshnessPolicy: {maximumLagMinutes: 60},
              hasAssetChecks: true,
            },
          },
        ],
      ]),
      // Add other required properties
      assets: [],
      assetGraphData: null,
    } as any);
  });

  describe('status filtering detection', () => {
    it('should detect when status filtering is needed', () => {
      mockParseExpression.mockReturnValue([{field: 'status', value: 'HEALTHY'} as any]);
      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {},
      } as any);

      renderHook(() => useAssetGraphSupplementaryData('status:HEALTHY', mockNodes), {
        wrapper: TestWrapper,
      });

      expect(mockUseAssetsHealthData).toHaveBeenCalledWith({
        assetKeys: [mockAssetKey1, mockAssetKey2],
        thread: 'AssetGraphSupplementaryData',
        blockTrace: false,
        skip: false,
      });
    });

    it('should skip health data when status filtering is not needed', () => {
      mockParseExpression.mockReturnValue([{field: 'key', value: 'asset1'} as any]);
      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {},
      } as any);

      renderHook(() => useAssetGraphSupplementaryData('key:asset1', mockNodes), {
        wrapper: TestWrapper,
      });

      expect(mockUseAssetsHealthData).toHaveBeenCalledWith({
        assetKeys: [mockAssetKey1, mockAssetKey2],
        thread: 'AssetGraphSupplementaryData',
        blockTrace: false,
        skip: true,
      });
    });

    it('should handle parse expression errors gracefully', () => {
      mockParseExpression.mockImplementation(() => {
        throw new Error('Parse error');
      });
      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {},
      } as any);

      renderHook(() => useAssetGraphSupplementaryData('invalid:expression', mockNodes), {
        wrapper: TestWrapper,
      });

      expect(mockUseAssetsHealthData).toHaveBeenCalledWith({
        assetKeys: [mockAssetKey1, mockAssetKey2],
        thread: 'AssetGraphSupplementaryData',
        blockTrace: false,
        skip: true,
      });
    });
  });

  describe('status categorization', () => {
    it('should categorize assets with all status types', async () => {
      const mockHealthData = buildAsset({
        key: mockAssetKey1,
        assetMaterializations: [],
        assetHealth: buildAssetHealth({
          assetHealth: AssetHealthStatus.HEALTHY,
          materializationStatus: AssetHealthStatus.HEALTHY,
          freshnessStatus: AssetHealthStatus.WARNING,
          assetChecksStatus: AssetHealthStatus.DEGRADED,
          materializationStatusMetadata: null,
          assetChecksStatusMetadata: null,
          freshnessStatusMetadata: null,
        }),
      });

      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {
          [JSON.stringify(mockAssetKey1.path)]: mockHealthData,
        },
      } as any);

      const {result} = renderHook(
        () => useAssetGraphSupplementaryData('status:HEALTHY', mockNodes.slice(0, 1)),
        {wrapper: TestWrapper},
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const data = result.current.data;

      // Should have entries for all status types
      const healthyKey = JSON.stringify({field: 'status', value: 'HEALTHY'});
      const materializationSuccessKey = JSON.stringify({
        field: 'status',
        value: 'MATERIALIZATION_SUCCESS',
      });
      const freshnessWarningKey = JSON.stringify({field: 'status', value: 'FRESHNESS_WARNING'});
      const checkFailureKey = JSON.stringify({field: 'status', value: 'CHECK_FAILURE'});

      expect(data).toBeDefined();
      expect(data?.[healthyKey]).toBeDefined();
      expect(data?.[healthyKey]).toContain(mockAssetKey1);
      expect(data?.[materializationSuccessKey]).toBeDefined();
      expect(data?.[materializationSuccessKey]).toContain(mockAssetKey1);
      expect(data?.[freshnessWarningKey]).toBeDefined();
      expect(data?.[freshnessWarningKey]).toContain(mockAssetKey1);
      expect(data?.[checkFailureKey]).toBeDefined();
      expect(data?.[checkFailureKey]).toContain(mockAssetKey1);
    });

    it('should handle missing health data', async () => {
      const mockHealthData = buildAsset({
        key: mockAssetKey1,
        assetHealth: null,
        assetMaterializations: [],
      });

      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {
          [JSON.stringify(mockAssetKey1.path)]: mockHealthData,
        },
      } as any);

      const {result} = renderHook(
        () => useAssetGraphSupplementaryData('status:UNKNOWN', mockNodes.slice(0, 1)),
        {wrapper: TestWrapper},
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const data = result.current.data;

      const unknownKey = JSON.stringify({field: 'status', value: 'UNKNOWN'});
      const materializationFailureKey = JSON.stringify({
        field: 'status',
        value: 'MATERIALIZATION_FAILURE',
      });
      const freshnessMissingKey = JSON.stringify({field: 'status', value: 'FRESHNESS_MISSING'});
      const checkMissingKey = JSON.stringify({field: 'status', value: 'CHECK_MISSING'});

      expect(data).toBeDefined();
      expect(data?.[unknownKey]).toBeDefined();
      expect(data?.[unknownKey]).toContain(mockAssetKey1);
      expect(data?.[materializationFailureKey]).toBeDefined();
      expect(data?.[materializationFailureKey]).toContain(mockAssetKey1);
      expect(data?.[freshnessMissingKey]).toBeDefined();
      expect(data?.[freshnessMissingKey]).toContain(mockAssetKey1);
      expect(data?.[checkMissingKey]).toBeDefined();
      expect(data?.[checkMissingKey]).toContain(mockAssetKey1);
    });
  });

  describe('loading states', () => {
    it('should return loading true when health data is incomplete', () => {
      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {
          // Only one asset when two are expected
          [JSON.stringify(mockAssetKey1.path)]: {
            key: mockAssetKey1,
            assetHealth: {assetHealth: AssetHealthStatus.HEALTHY},
          },
        },
      } as any);

      const {result} = renderHook(
        () => useAssetGraphSupplementaryData('status:HEALTHY', mockNodes),
        {wrapper: TestWrapper},
      );

      expect(result.current.loading).toBe(true);
      expect(result.current.data).toEqual({});
    });

    it('should return loading false when all data is loaded', async () => {
      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {
          [JSON.stringify(mockAssetKey1.path)]: {
            key: mockAssetKey1,
            assetHealth: {assetHealth: AssetHealthStatus.HEALTHY},
          },
          [JSON.stringify(mockAssetKey2.path)]: {
            key: mockAssetKey2,
            assetHealth: {assetHealth: AssetHealthStatus.DEGRADED},
          },
        },
      } as any);

      const {result} = renderHook(
        () => useAssetGraphSupplementaryData('status:HEALTHY', mockNodes),
        {wrapper: TestWrapper},
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.data).not.toEqual({});
    });
  });
});

describe('getMaterializationStatus', () => {
  it('should return correct materialization statuses based on health data', async () => {
    const mockAssetKey1 = buildAssetKey({path: ['asset1']});

    const testCases = [
      {
        healthStatus: AssetHealthStatus.HEALTHY,
        expectedStatus: 'MATERIALIZATION_SUCCESS',
      },
      {
        healthStatus: AssetHealthStatus.UNKNOWN,
        expectedStatus: 'MATERIALIZATION_UNKNOWN',
      },
      {
        healthStatus: AssetHealthStatus.DEGRADED,
        expectedStatus: 'MATERIALIZATION_FAILURE',
      },
      {
        healthStatus: AssetHealthStatus.WARNING,
        expectedStatus: 'MATERIALIZATION_FAILURE',
      },
    ];

    for (const {healthStatus, expectedStatus} of testCases) {
      mockUseAllAssets.mockReturnValue({
        assetsByAssetKey: new Map([
          [
            JSON.stringify(['asset1']),
            {
              definition: {
                internalFreshnessPolicy: null,
                hasAssetChecks: false,
              },
            },
          ],
        ]),
        assets: [],
        assetGraphData: null,
      } as any);

      const mockHealthData = buildAsset({
        key: mockAssetKey1,
        assetMaterializations: [],
        assetHealth: buildAssetHealth({
          assetHealth: AssetHealthStatus.HEALTHY,
          materializationStatus: healthStatus,
          freshnessStatus: AssetHealthStatus.HEALTHY,
          assetChecksStatus: AssetHealthStatus.HEALTHY,
          materializationStatusMetadata: null,
          assetChecksStatusMetadata: null,
          freshnessStatusMetadata: null,
        }),
      });

      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {
          [JSON.stringify(mockAssetKey1.path)]: mockHealthData,
        },
      } as any);

      const mockNodes = [
        {
          assetKey: mockAssetKey1,
        } as WorkspaceAssetFragment,
      ];

      const {result} = renderHook(
        () => useAssetGraphSupplementaryData('status:HEALTHY', mockNodes),
        {wrapper: TestWrapper},
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const expectedKey = JSON.stringify({field: 'status', value: expectedStatus});
      expect(result.current.data).toBeDefined();
      expect(result.current.data?.[expectedKey]).toBeDefined();
      expect(result.current.data?.[expectedKey]).toContain(mockAssetKey1);
    }
  });
});

describe('getFreshnessStatus', () => {
  it('should return correct freshness statuses based on health data and asset definition', async () => {
    const mockAssetKey1 = buildAssetKey({path: ['asset1']});

    const testCases = [
      {
        healthStatus: AssetHealthStatus.HEALTHY,
        hasPolicy: false,
        expectedStatus: 'FRESHNESS_PASSING',
      },
      {
        healthStatus: AssetHealthStatus.WARNING,
        hasPolicy: false,
        expectedStatus: 'FRESHNESS_WARNING',
      },
      {
        healthStatus: AssetHealthStatus.DEGRADED,
        hasPolicy: false,
        expectedStatus: 'FRESHNESS_FAILURE',
      },
      {
        healthStatus: AssetHealthStatus.UNKNOWN,
        hasPolicy: true,
        expectedStatus: 'FRESHNESS_UNKNOWN',
      },
      {
        healthStatus: AssetHealthStatus.UNKNOWN,
        hasPolicy: false,
        expectedStatus: 'FRESHNESS_MISSING',
      },
    ];

    for (const {healthStatus, hasPolicy, expectedStatus} of testCases) {
      mockUseAllAssets.mockReturnValue({
        assetsByAssetKey: new Map([
          [
            JSON.stringify(['asset1']),
            {
              definition: {
                internalFreshnessPolicy: hasPolicy ? {maximumLagMinutes: 60} : null,
                hasAssetChecks: false,
              },
            },
          ],
        ]),
        assets: [],
        assetGraphData: null,
      } as any);

      const mockHealthData = buildAsset({
        key: mockAssetKey1,
        assetMaterializations: [],
        assetHealth: buildAssetHealth({
          assetHealth: AssetHealthStatus.HEALTHY,
          materializationStatus: AssetHealthStatus.HEALTHY,
          freshnessStatus: healthStatus,
          assetChecksStatus: AssetHealthStatus.HEALTHY,
          materializationStatusMetadata: null,
          assetChecksStatusMetadata: null,
          freshnessStatusMetadata: null,
        }),
      });

      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {
          [JSON.stringify(mockAssetKey1.path)]: mockHealthData,
        },
      } as any);

      const mockNodes = [
        {
          assetKey: mockAssetKey1,
        } as WorkspaceAssetFragment,
      ];

      const {result} = renderHook(
        () => useAssetGraphSupplementaryData('status:HEALTHY', mockNodes),
        {wrapper: TestWrapper},
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const expectedKey = JSON.stringify({field: 'status', value: expectedStatus});
      expect(result.current.data).toBeDefined();
      expect(result.current.data?.[expectedKey]).toBeDefined();
      expect(result.current.data?.[expectedKey]).toContain(mockAssetKey1);
    }
  });
});

describe('getCheckStatus', () => {
  it('should return correct check statuses based on health data and asset definition', async () => {
    const mockAssetKey1 = buildAssetKey({path: ['asset1']});

    const testCases = [
      {
        healthStatus: AssetHealthStatus.HEALTHY,
        hasChecks: false,
        expectedStatus: 'CHECK_PASSING',
      },
      {
        healthStatus: AssetHealthStatus.WARNING,
        hasChecks: false,
        expectedStatus: 'CHECK_WARNING',
      },
      {
        healthStatus: AssetHealthStatus.DEGRADED,
        hasChecks: false,
        expectedStatus: 'CHECK_FAILURE',
      },
      {
        healthStatus: AssetHealthStatus.UNKNOWN,
        hasChecks: true,
        expectedStatus: 'CHECK_UNKNOWN',
      },
      {
        healthStatus: AssetHealthStatus.UNKNOWN,
        hasChecks: false,
        expectedStatus: 'CHECK_MISSING',
      },
    ];

    for (const {healthStatus, hasChecks, expectedStatus} of testCases) {
      mockUseAllAssets.mockReturnValue({
        assetsByAssetKey: new Map([
          [
            JSON.stringify(['asset1']),
            {
              definition: {
                internalFreshnessPolicy: null,
                hasAssetChecks: hasChecks,
              },
            },
          ],
        ]),
        assets: [],
        assetGraphData: null,
      } as any);

      const mockHealthData = buildAsset({
        key: mockAssetKey1,
        assetMaterializations: [],
        assetHealth: buildAssetHealth({
          assetHealth: AssetHealthStatus.HEALTHY,
          materializationStatus: AssetHealthStatus.HEALTHY,
          freshnessStatus: AssetHealthStatus.HEALTHY,
          assetChecksStatus: healthStatus,
          materializationStatusMetadata: null,
          assetChecksStatusMetadata: null,
          freshnessStatusMetadata: null,
        }),
      });

      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {
          [JSON.stringify(mockAssetKey1.path)]: mockHealthData,
        },
      } as any);

      const mockNodes = [
        {
          assetKey: mockAssetKey1,
        } as WorkspaceAssetFragment,
      ];

      const {result} = renderHook(
        () => useAssetGraphSupplementaryData('status:HEALTHY', mockNodes),
        {wrapper: TestWrapper},
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const expectedKey = JSON.stringify({field: 'status', value: expectedStatus});
      expect(result.current.data).toBeDefined();
      expect(result.current.data?.[expectedKey]).toBeDefined();
      expect(result.current.data?.[expectedKey]).toContain(mockAssetKey1);
    }
  });
});
