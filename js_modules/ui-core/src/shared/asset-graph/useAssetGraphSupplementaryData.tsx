import {useMemo} from 'react';

import {gql, useQuery} from '../../apollo-client';
import {
  AssetInstigatorsQuery,
  AssetInstigatorsQueryVariables,
} from './types/useAssetGraphSupplementaryData.types';
import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {parseExpression} from '../../asset-selection/AssetSelectionSupplementaryDataVisitor';
import {SupplementaryInformation} from '../../asset-selection/types';
import {getSupplementaryDataKey} from '../../asset-selection/util';
import {AssetKey} from '../../assets/types';
import {Asset, WorkspaceAssetNode, useAllAssets} from '../../assets/useAllAssets';
import {AssetHealthStatus, InstigationStatus, SensorType} from '../../graphql/types';
import {useStableReferenceByHash} from '../../hooks/useStableReferenceByHash';

const emptyObject = {} as SupplementaryInformation;
export const useAssetGraphSupplementaryData = (
  selection: string,
  nodes: WorkspaceAssetNode[],
): {loading: boolean; data: SupplementaryInformation} => {
  const parsedFilters = useMemo(() => {
    try {
      return parseExpression(selection);
    } catch {
      return [];
    }
  }, [selection]);

  const needsAssetHealthData = useMemo(
    () => parsedFilters.some((filter) => filter.field === 'status'),
    [parsedFilters],
  );

  const needsAutomationData = useMemo(
    () =>
      parsedFilters.some(
        (filter) =>
          filter.field === 'automation_type' ||
          filter.field === 'sensor' ||
          filter.field === 'schedule',
      ),
    [parsedFilters],
  );

  const assetKeys = useMemo(() => nodes.map((node) => node.assetKey), [nodes]);

  const {liveDataByNode} = useAssetsHealthData({
    assetKeys,
    thread: 'AssetGraphSupplementaryData',
    blockTrace: false,
    skip: !needsAssetHealthData,
  });

  // Note: This intentionally does not use useAssetsAutomationData. That hook is fine
  // for a small number of displayed assets, but `nodes` here is all assets in a repo
  // or all repos. Because 1 sensor has many targeted assets, querying per-asset loads
  // the same sensor data thousands of times. Querying the other way (sensors[].assetSelection)
  // is about 100x faster. It's possible we should get rid of useAssetsAutomationData
  // entirely.
  const {data: instigatorsData, loading: instigatorsLoading} = useQuery<
    AssetInstigatorsQuery,
    AssetInstigatorsQueryVariables
  >(ASSET_INSTIGATORS_QUERY, {skip: !needsAutomationData});

  const {assetsByAssetKey} = useAllAssets();

  const healthLoading = needsAssetHealthData
    ? Object.keys(liveDataByNode).length !== nodes.length
    : false;

  const automationLoading = needsAutomationData ? instigatorsLoading : false;

  const loading = healthLoading || automationLoading;

  const assetsByStatus = useMemo(() => {
    if (healthLoading) {
      return emptyObject;
    }
    if (!needsAssetHealthData) {
      return emptyObject;
    }
    return Object.values(liveDataByNode).reduce(
      (acc, liveData) => {
        const status = liveData.assetHealth?.assetHealth ?? 'UNKNOWN';
        const asset = assetsByAssetKey.get(tokenForAssetKey(liveData.key)) ?? null;
        const materializationStatus = getMaterializationStatus(liveData, asset);
        const freshnessStatus = getFreshnessStatus(liveData, asset);
        const checkStatus = getCheckStatus(liveData, asset);

        function addStatusValue(value: string) {
          const supplementaryDataKey = getSupplementaryDataKey({
            field: 'status',
            value,
          });
          acc[supplementaryDataKey] = acc[supplementaryDataKey] || [];
          acc[supplementaryDataKey].push(liveData.key);
        }

        addStatusValue(status);
        addStatusValue(materializationStatus);
        addStatusValue(freshnessStatus);
        addStatusValue(checkStatus);
        return acc;
      },
      {} as Record<string, AssetKey[]>,
    );
  }, [assetsByAssetKey, liveDataByNode, healthLoading, needsAssetHealthData]);

  const assetsByAutomationType = useMemo(() => {
    if (automationLoading || !needsAutomationData || !instigatorsData) {
      return emptyObject;
    }
    return buildAutomationTypeSupplementaryData(instigatorsData, nodes);
  }, [instigatorsData, nodes, automationLoading, needsAutomationData]);

  const mergedData = useMemo(() => {
    if (loading) {
      return emptyObject;
    }
    return {...assetsByStatus, ...assetsByAutomationType};
  }, [loading, assetsByStatus, assetsByAutomationType]);

  const data = useStableReferenceByHash(mergedData);

  return {
    loading,
    data: loading ? emptyObject : data,
  };
};

export function getMaterializationStatus(healthData: AssetHealthFragment, _asset: Asset | null) {
  if (healthData.assetHealth?.materializationStatus === AssetHealthStatus.HEALTHY) {
    return 'MATERIALIZATION_SUCCESS';
  }
  if (healthData.assetHealth?.materializationStatus === AssetHealthStatus.UNKNOWN) {
    return 'MATERIALIZATION_UNKNOWN';
  }
  return 'MATERIALIZATION_FAILURE';
}

export function getFreshnessStatus(healthData: AssetHealthFragment, asset: Asset | null) {
  if (healthData.assetHealth?.freshnessStatus === AssetHealthStatus.HEALTHY) {
    return 'FRESHNESS_PASSING';
  }
  if (healthData.assetHealth?.freshnessStatus === AssetHealthStatus.WARNING) {
    return 'FRESHNESS_WARNING';
  }
  if (healthData.assetHealth?.freshnessStatus === AssetHealthStatus.DEGRADED) {
    return 'FRESHNESS_FAILURE';
  }
  if (asset?.definition?.internalFreshnessPolicy) {
    return 'FRESHNESS_UNKNOWN';
  }
  return 'FRESHNESS_MISSING';
}

export function getCheckStatus(healthData: AssetHealthFragment, asset: Asset | null) {
  if (healthData.assetHealth?.assetChecksStatus === AssetHealthStatus.HEALTHY) {
    return 'CHECK_PASSING';
  }
  if (healthData.assetHealth?.assetChecksStatus === AssetHealthStatus.WARNING) {
    return 'CHECK_WARNING';
  }
  if (healthData.assetHealth?.assetChecksStatus === AssetHealthStatus.DEGRADED) {
    return 'CHECK_FAILURE';
  }
  if (asset?.definition?.hasAssetChecks) {
    return 'CHECK_UNKNOWN';
  }
  return 'CHECK_MISSING';
}

const SENSOR_TYPE_TO_VALUE: Record<SensorType, string | null> = {
  [SensorType.STANDARD]: 'sensor/standard',
  [SensorType.RUN_STATUS]: 'sensor/run_status',
  [SensorType.ASSET]: 'sensor/asset',
  [SensorType.MULTI_ASSET]: 'sensor/multi_asset',
  [SensorType.AUTOMATION]: 'sensor/automation_condition',
  [SensorType.AUTO_MATERIALIZE]: 'sensor/automation_condition',
  [SensorType.FRESHNESS_POLICY]: null, // deprecated
  [SensorType.UNKNOWN]: 'sensor/unknown',
};

type InstigatorInfo =
  | {type: 'schedule'; name: string; status: InstigationStatus}
  | {type: 'sensor'; name: string; sensorType: SensorType};

export function buildAutomationTypeSupplementaryData(
  queryData: AssetInstigatorsQuery,
  nodes: WorkspaceAssetNode[],
): Record<string, AssetKey[]> {
  // Index assets by (repository id, job name) so we can resolve jobs that
  // a sensor or schedule targets back to the assets defined in them. Job
  // names are only unique within a repository, so we scope by repo id.
  const assetKeysByRepoAndJob = new Map<string, Map<string, AssetKey[]>>();
  for (const node of nodes) {
    const repoId = node.repository.id;
    let jobMap = assetKeysByRepoAndJob.get(repoId);
    if (!jobMap) {
      jobMap = new Map<string, AssetKey[]>();
      assetKeysByRepoAndJob.set(repoId, jobMap);
    }
    for (const jobName of node.jobNames) {
      let keys = jobMap.get(jobName);
      if (!keys) {
        keys = [];
        jobMap.set(jobName, keys);
      }
      keys.push(node.assetKey);
    }
  }

  // Build a map from asset key token → instigators targeting it.
  const instigatorsByAssetToken = new Map<string, InstigatorInfo[]>();

  function pushInstigator(assetKey: AssetKey, info: InstigatorInfo) {
    const token = tokenForAssetKey(assetKey);
    let list = instigatorsByAssetToken.get(token);
    if (!list) {
      list = [];
      instigatorsByAssetToken.set(token, list);
    }
    list.push(info);
  }

  if (queryData.repositoriesOrError.__typename === 'RepositoryConnection') {
    for (const repo of queryData.repositoriesOrError.nodes) {
      const jobsInRepo = assetKeysByRepoAndJob.get(repo.id);
      for (const sensor of repo.sensors) {
        const info: InstigatorInfo = {
          type: 'sensor',
          name: sensor.name,
          sensorType: sensor.sensorType,
        };
        // An explicit asset selection is authoritative. Skip targets in
        // that case, since sensor.targets often points at the synthetic
        // root asset job, which would pull in assets that aren't actually
        // part of the automation's scope.
        if (sensor.assetSelection) {
          for (const assetKey of sensor.assetSelection.assetKeys) {
            pushInstigator(assetKey, info);
          }
        } else if (sensor.targets && jobsInRepo) {
          for (const target of sensor.targets) {
            if (!target.pipelineName) {
              continue;
            }
            const assetKeys = jobsInRepo.get(target.pipelineName);
            if (!assetKeys) {
              continue;
            }
            for (const assetKey of assetKeys) {
              pushInstigator(assetKey, info);
            }
          }
        }
      }
      for (const schedule of repo.schedules) {
        const info: InstigatorInfo = {
          type: 'schedule',
          name: schedule.name,
          status: schedule.scheduleState.status,
        };
        if (schedule.assetSelection) {
          for (const assetKey of schedule.assetSelection.assetKeys) {
            pushInstigator(assetKey, info);
          }
        } else if (jobsInRepo && schedule.pipelineName) {
          const assetKeys = jobsInRepo.get(schedule.pipelineName);
          if (assetKeys) {
            for (const assetKey of assetKeys) {
              pushInstigator(assetKey, info);
            }
          }
        }
      }
    }
  }

  // Accumulate into Sets so the same asset doesn't land in a bucket twice
  // when the same node iteration path adds it via multiple instigators.
  const acc: Record<string, Set<AssetKey>> = {};

  function addValue(field: string, value: string, key: AssetKey) {
    const supplementaryDataKey = getSupplementaryDataKey({field, value});
    let existing = acc[supplementaryDataKey];
    if (!existing) {
      existing = new Set<AssetKey>();
      acc[supplementaryDataKey] = existing;
    }
    existing.add(key);
  }

  for (const node of nodes) {
    const token = tokenForAssetKey(node.assetKey);
    const instigators = instigatorsByAssetToken.get(token) || [];

    if (instigators.length === 0) {
      addValue('automation_type', 'none', node.assetKey);
      continue;
    }

    // Has at least one automation
    addValue('automation_type', 'any', node.assetKey);

    const hasDisabled = instigators.some(
      (i) => i.type === 'schedule' && i.status === InstigationStatus.STOPPED,
    );
    if (hasDisabled) {
      addValue('automation_type', 'disabled', node.assetKey);
    }

    for (const instigator of instigators) {
      if (instigator.type === 'schedule') {
        addValue('automation_type', 'schedule', node.assetKey);
        // Index by schedule name for schedule: filter
        addValue('schedule', instigator.name, node.assetKey);
      } else {
        addValue('automation_type', 'sensor', node.assetKey);
        // Index by sensor name for sensor: filter
        addValue('sensor', instigator.name, node.assetKey);
        const sensorValue = SENSOR_TYPE_TO_VALUE[instigator.sensorType];
        if (sensorValue) {
          addValue('automation_type', sensorValue, node.assetKey);
        }
      }
    }
  }

  const result: Record<string, AssetKey[]> = {};
  for (const [key, value] of Object.entries(acc)) {
    result[key] = Array.from(value);
  }
  return result;
}

const ASSET_INSTIGATORS_QUERY = gql`
  query AssetInstigatorsQuery {
    repositoriesOrError {
      ... on RepositoryConnection {
        nodes {
          id
          sensors {
            id
            name
            sensorType
            assetSelection {
              assetKeys {
                path
              }
            }
            targets {
              pipelineName
            }
          }
          schedules {
            id
            name
            pipelineName
            assetSelection {
              assetKeys {
                path
              }
            }
            scheduleState {
              id
              status
            }
          }
        }
      }
    }
  }
`;
