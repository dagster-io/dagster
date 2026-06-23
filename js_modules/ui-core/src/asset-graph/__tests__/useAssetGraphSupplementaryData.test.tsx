import {MockedProvider} from '@apollo/client/testing';
import {AssetInstigatorsQuery} from '@shared/asset-graph/types/useAssetGraphSupplementaryData.types';
import {
  buildAutomationTypeSupplementaryData,
  useAssetGraphSupplementaryData,
} from '@shared/asset-graph/useAssetGraphSupplementaryData';
import {renderHook, waitFor} from '@testing-library/react';
import React from 'react';

import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {
  Filter,
  parseExpression,
} from '../../asset-selection/AssetSelectionSupplementaryDataVisitor';
import {getSupplementaryDataKey} from '../../asset-selection/util';
import {WorkspaceAssetNode, useAllAssets} from '../../assets/useAllAssets';
import {
  buildAsset,
  buildAssetHealth,
  buildAssetKey,
  buildAssetNode,
  buildAssetSelection,
  buildInstigationState,
  buildQuery,
  buildRepository,
  buildRepositoryConnection,
  buildRepositoryLocation,
  buildSchedule,
  buildSensor,
  buildTarget,
} from '../../graphql/builders';
import {AssetHealthStatus, InstigationStatus, SensorType} from '../../graphql/types';

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

  const mockNodes: WorkspaceAssetNode[] = [
    {
      assetKey: mockAssetKey1,
      // Add other required properties for WorkspaceAssetNode
    } as WorkspaceAssetNode,
    {
      assetKey: mockAssetKey2,
    } as WorkspaceAssetNode,
  ];

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockParseExpression.mockReturnValue([{field: 'status', value: 'HEALTHY'}]);
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
    } as unknown as ReturnType<typeof useAllAssets>);
  });

  describe('status filtering detection', () => {
    it('should detect when status filtering is needed', () => {
      mockParseExpression.mockReturnValue([{field: 'status', value: 'HEALTHY'}]);
      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {},
      } as unknown as ReturnType<typeof useAssetsHealthData>);

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
      mockParseExpression.mockReturnValue([{field: 'key', value: 'asset1'} as unknown as Filter]);
      mockUseAssetsHealthData.mockReturnValue({
        liveDataByNode: {},
      } as unknown as ReturnType<typeof useAssetsHealthData>);

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
      } as unknown as ReturnType<typeof useAssetsHealthData>);

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
      } as unknown as ReturnType<typeof useAssetsHealthData>);

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
      } as unknown as ReturnType<typeof useAssetsHealthData>);

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
      } as unknown as ReturnType<typeof useAssetsHealthData>);

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
      } as unknown as ReturnType<typeof useAssetsHealthData>);

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
      } as unknown as ReturnType<typeof useAllAssets>);

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
      } as unknown as ReturnType<typeof useAssetsHealthData>);

      const mockNodes = [
        {
          assetKey: mockAssetKey1,
        } as WorkspaceAssetNode,
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
      } as unknown as ReturnType<typeof useAllAssets>);

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
      } as unknown as ReturnType<typeof useAssetsHealthData>);

      const mockNodes = [
        {
          assetKey: mockAssetKey1,
        } as WorkspaceAssetNode,
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

describe('buildAutomationTypeSupplementaryData', () => {
  type NodeOverrides = {
    path: string[];
    repoId: string;
    jobNames?: string[];
  };

  function makeNode({path, repoId, jobNames = []}: NodeOverrides): WorkspaceAssetNode {
    return buildAssetNode({
      assetKey: buildAssetKey({path}),
      jobNames,
      repository: buildRepository({
        id: repoId,
        name: repoId,
        location: buildRepositoryLocation({id: `${repoId}-location`, name: repoId}),
      }),
    }) as unknown as WorkspaceAssetNode;
  }

  type SensorOverrides = {
    name: string;
    sensorType?: SensorType;
    assetKeys?: Array<{path: string[]}>;
    targets?: string[];
  };

  function makeSensor({
    name,
    sensorType = SensorType.STANDARD,
    assetKeys,
    targets,
  }: SensorOverrides) {
    return buildSensor({
      id: name,
      name,
      sensorType,
      assetSelection: assetKeys
        ? buildAssetSelection({
            assetKeys: assetKeys.map((k) => buildAssetKey({path: k.path})),
          })
        : null,
      targets: targets ? targets.map((pipelineName) => buildTarget({pipelineName})) : null,
    });
  }

  type ScheduleOverrides = {
    name: string;
    pipelineName: string;
    assetKeys?: Array<{path: string[]}>;
    status?: InstigationStatus;
  };

  function makeSchedule({
    name,
    pipelineName,
    assetKeys,
    status = InstigationStatus.RUNNING,
  }: ScheduleOverrides) {
    return buildSchedule({
      id: name,
      name,
      pipelineName,
      assetSelection: assetKeys
        ? buildAssetSelection({
            assetKeys: assetKeys.map((k) => buildAssetKey({path: k.path})),
          })
        : null,
      scheduleState: buildInstigationState({id: `${name}-state`, status}),
    });
  }

  function makeQuery(
    repos: Array<{
      id: string;
      sensors?: ReturnType<typeof makeSensor>[];
      schedules?: ReturnType<typeof makeSchedule>[];
    }>,
  ): AssetInstigatorsQuery {
    return buildQuery({
      repositoriesOrError: buildRepositoryConnection({
        nodes: repos.map((r) =>
          buildRepository({
            id: r.id,
            sensors: r.sensors ?? [],
            schedules: r.schedules ?? [],
          }),
        ),
      }),
    }) as unknown as AssetInstigatorsQuery;
  }

  const key = (field: string, value: string) => getSupplementaryDataKey({field, value});

  it('returns automation_type:none for assets with no matching instigators', () => {
    const node = makeNode({path: ['lonely'], repoId: 'repo-a'});
    const result = buildAutomationTypeSupplementaryData(makeQuery([{id: 'repo-a'}]), [node]);

    expect(result[key('automation_type', 'none')]).toEqual([node.assetKey]);
    expect(result[key('automation_type', 'any')]).toBeUndefined();
  });

  it('matches assets via assetSelection for sensors and schedules', () => {
    const nodeA = makeNode({path: ['a'], repoId: 'repo-a'});
    const nodeB = makeNode({path: ['b'], repoId: 'repo-a'});
    const query = makeQuery([
      {
        id: 'repo-a',
        sensors: [makeSensor({name: 'sensor1', assetKeys: [{path: ['a']}]})],
        schedules: [
          makeSchedule({name: 'schedule1', pipelineName: 'unused', assetKeys: [{path: ['b']}]}),
        ],
      },
    ]);

    const result = buildAutomationTypeSupplementaryData(query, [nodeA, nodeB]);

    expect(result[key('sensor', 'sensor1')]).toEqual([nodeA.assetKey]);
    expect(result[key('schedule', 'schedule1')]).toEqual([nodeB.assetKey]);
    expect(result[key('automation_type', 'sensor')]).toEqual([nodeA.assetKey]);
    expect(result[key('automation_type', 'schedule')]).toEqual([nodeB.assetKey]);
    expect(result[key('automation_type', 'any')]).toEqual([nodeA.assetKey, nodeB.assetKey]);
  });

  it('resolves targeted jobs back to assets within the same repository', () => {
    const nodeA = makeNode({path: ['a'], repoId: 'repo-a', jobNames: ['my_job']});
    const nodeB = makeNode({path: ['b'], repoId: 'repo-a', jobNames: ['my_job']});
    const nodeC = makeNode({path: ['c'], repoId: 'repo-a', jobNames: ['other_job']});
    const query = makeQuery([
      {
        id: 'repo-a',
        sensors: [makeSensor({name: 'sensor1', targets: ['my_job']})],
        schedules: [makeSchedule({name: 'schedule1', pipelineName: 'other_job'})],
      },
    ]);

    const result = buildAutomationTypeSupplementaryData(query, [nodeA, nodeB, nodeC]);

    expect(result[key('sensor', 'sensor1')]).toEqual([nodeA.assetKey, nodeB.assetKey]);
    expect(result[key('schedule', 'schedule1')]).toEqual([nodeC.assetKey]);
  });

  it('disambiguates same-named jobs across repositories', () => {
    // Both repos have a job called "shared_job" but the schedule in repo-a
    // must only pick up repo-a's asset.
    const assetInRepoA = makeNode({
      path: ['in_a'],
      repoId: 'repo-a',
      jobNames: ['shared_job'],
    });
    const assetInRepoB = makeNode({
      path: ['in_b'],
      repoId: 'repo-b',
      jobNames: ['shared_job'],
    });
    const query = makeQuery([
      {
        id: 'repo-a',
        schedules: [makeSchedule({name: 'schedule_a', pipelineName: 'shared_job'})],
      },
      {
        id: 'repo-b',
        sensors: [makeSensor({name: 'sensor_b', targets: ['shared_job']})],
      },
    ]);

    const result = buildAutomationTypeSupplementaryData(query, [assetInRepoA, assetInRepoB]);

    expect(result[key('schedule', 'schedule_a')]).toEqual([assetInRepoA.assetKey]);
    expect(result[key('sensor', 'sensor_b')]).toEqual([assetInRepoB.assetKey]);
  });

  it('prefers assetSelection over targets/pipelineName when both are present', () => {
    // sensor1 sets assetSelection=[a] AND targets=[my_job]. my_job also
    // contains asset b. Under the precedence rule, targets is ignored when
    // assetSelection is set — Dagster commonly populates targets with a
    // synthetic root asset job whose scope shouldn't drive automation_type.
    // schedule1 behaves the same way for pipelineName vs. assetSelection.
    const nodeA = makeNode({path: ['a'], repoId: 'repo-a', jobNames: ['my_job']});
    const nodeB = makeNode({path: ['b'], repoId: 'repo-a', jobNames: ['my_job']});
    const query = makeQuery([
      {
        id: 'repo-a',
        sensors: [makeSensor({name: 'sensor1', assetKeys: [{path: ['a']}], targets: ['my_job']})],
        schedules: [
          makeSchedule({
            name: 'schedule1',
            pipelineName: 'my_job',
            assetKeys: [{path: ['a']}],
          }),
        ],
      },
    ]);

    const result = buildAutomationTypeSupplementaryData(query, [nodeA, nodeB]);

    expect(result[key('sensor', 'sensor1')]).toEqual([nodeA.assetKey]);
    expect(result[key('schedule', 'schedule1')]).toEqual([nodeA.assetKey]);
    // b is inside my_job but not in either assetSelection, so it should
    // stay in the automation_type:none bucket.
    expect(result[key('automation_type', 'none')]).toEqual([nodeB.assetKey]);
  });

  it('flags assets as disabled when reached by a stopped schedule', () => {
    const nodeA = makeNode({path: ['a'], repoId: 'repo-a', jobNames: ['my_job']});
    const query = makeQuery([
      {
        id: 'repo-a',
        schedules: [
          makeSchedule({
            name: 'stopped_schedule',
            pipelineName: 'my_job',
            status: InstigationStatus.STOPPED,
          }),
        ],
      },
    ]);

    const result = buildAutomationTypeSupplementaryData(query, [nodeA]);

    expect(result[key('automation_type', 'disabled')]).toEqual([nodeA.assetKey]);
    expect(result[key('automation_type', 'any')]).toEqual([nodeA.assetKey]);
  });

  it('maps sensor types to finer-grained automation_type buckets', () => {
    const nodeA = makeNode({path: ['a'], repoId: 'repo-a'});
    const nodeB = makeNode({path: ['b'], repoId: 'repo-a'});
    const query = makeQuery([
      {
        id: 'repo-a',
        sensors: [
          makeSensor({
            name: 'standard_sensor',
            sensorType: SensorType.STANDARD,
            assetKeys: [{path: ['a']}],
          }),
          makeSensor({
            name: 'automation_sensor',
            sensorType: SensorType.AUTOMATION,
            assetKeys: [{path: ['b']}],
          }),
        ],
      },
    ]);

    const result = buildAutomationTypeSupplementaryData(query, [nodeA, nodeB]);

    expect(result[key('automation_type', 'sensor/standard')]).toEqual([nodeA.assetKey]);
    expect(result[key('automation_type', 'sensor/automation_condition')]).toEqual([nodeB.assetKey]);
  });

  it('covers the full picture across sensors, schedules, jobs, and repos', () => {
    const a1 = makeNode({path: ['a1'], repoId: 'repo-a', jobNames: ['job1']});
    const a2 = makeNode({path: ['a2'], repoId: 'repo-a', jobNames: ['job1']});
    const a3 = makeNode({path: ['a3'], repoId: 'repo-a', jobNames: ['job2']});
    const a4 = makeNode({path: ['a4'], repoId: 'repo-a'});
    const b1 = makeNode({path: ['b1'], repoId: 'repo-b', jobNames: ['job1']});

    const query = makeQuery([
      {
        id: 'repo-a',
        sensors: [
          // Selection-based sensor.
          makeSensor({
            name: 'selection_sensor',
            sensorType: SensorType.ASSET,
            assetKeys: [{path: ['a1']}],
          }),
          // Target-based sensor with no assetSelection.
          makeSensor({
            name: 'target_sensor',
            sensorType: SensorType.STANDARD,
            targets: ['job2'],
          }),
        ],
        schedules: [
          // Target-based, stopped.
          makeSchedule({
            name: 'stopped_schedule',
            pipelineName: 'job1',
            status: InstigationStatus.STOPPED,
          }),
        ],
      },
      {
        id: 'repo-b',
        schedules: [makeSchedule({name: 'schedule_b', pipelineName: 'job1'})],
      },
    ]);

    const result = buildAutomationTypeSupplementaryData(query, [a1, a2, a3, a4, b1]);

    expect(result[key('automation_type', 'none')]).toEqual([a4.assetKey]);
    expect(result[key('automation_type', 'any')]).toEqual([
      a1.assetKey,
      a2.assetKey,
      a3.assetKey,
      b1.assetKey,
    ]);
    // stopped_schedule covers a1 and a2 via pipelineName='job1'.
    expect(result[key('automation_type', 'disabled')]).toEqual([a1.assetKey, a2.assetKey]);
    // selection_sensor → a1, target_sensor → a3.
    expect(result[key('automation_type', 'sensor')]).toEqual([a1.assetKey, a3.assetKey]);
    expect(result[key('automation_type', 'sensor/asset')]).toEqual([a1.assetKey]);
    expect(result[key('automation_type', 'sensor/standard')]).toEqual([a3.assetKey]);
    // stopped_schedule (a1, a2) + schedule_b (b1).
    expect(result[key('automation_type', 'schedule')]).toEqual([
      a1.assetKey,
      a2.assetKey,
      b1.assetKey,
    ]);
    expect(result[key('sensor', 'selection_sensor')]).toEqual([a1.assetKey]);
    expect(result[key('sensor', 'target_sensor')]).toEqual([a3.assetKey]);
    expect(result[key('schedule', 'stopped_schedule')]).toEqual([a1.assetKey, a2.assetKey]);
    // Repo disambiguation: schedule_b only picks up b1, not a1/a2.
    expect(result[key('schedule', 'schedule_b')]).toEqual([b1.assetKey]);
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
      } as unknown as ReturnType<typeof useAllAssets>);

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
      } as unknown as ReturnType<typeof useAssetsHealthData>);

      const mockNodes = [
        {
          assetKey: mockAssetKey1,
        } as WorkspaceAssetNode,
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
