import {Box} from '@dagster-io/ui';
import React from 'react';

import {AssetNodeFragmentFragment, RunStatus} from '../graphql/graphql';

import {AssetNode, AssetNodeMinimal} from './AssetNode';
import {LiveDataForNode} from './Utils';

const ASSET_NODE_DEFINITION: AssetNodeFragmentFragment = {
  __typename: 'AssetNode',
  assetKey: {__typename: 'AssetKey', path: ['asset1']},
  computeKind: null,
  description: 'This is a test asset description',
  graphName: null,
  id: '["asset1"]',
  isObservable: false,
  isPartitioned: false,
  isSource: false,
  jobNames: ['job1'],
  opNames: ['asset1'],
  opVersion: '1',
};

const SOURCE_ASSET_NODE_DEFINITION: AssetNodeFragmentFragment = {
  __typename: 'AssetNode',
  assetKey: {__typename: 'AssetKey', path: ['source_asset']},
  computeKind: null,
  description: 'This is a test source asset',
  graphName: null,
  id: '["source_asset"]',
  isObservable: true,
  isPartitioned: false,
  isSource: true,
  jobNames: [],
  opNames: [],
  opVersion: '1',
};

// eslint-disable-next-line import/no-default-export
export default {component: AssetNode};

export const LiveStates = () => {
  const caseWithLiveData = (
    name: string,
    liveData: LiveDataForNode | undefined = undefined,
    def: AssetNodeFragmentFragment = ASSET_NODE_DEFINITION,
  ) => {
    return (
      <Box flex={{direction: 'column', gap: 0, alignItems: 'flex-start'}}>
        <div style={{position: 'relative', width: 280}}>
          <AssetNode definition={def} selected={false} liveData={liveData} />
        </div>
        <div style={{position: 'relative', width: 280, height: 82}}>
          <div style={{position: 'absolute', width: 280, height: 82}}>
            <AssetNodeMinimal definition={def} selected={false} liveData={liveData} />
          </div>
        </div>
        <code>
          <strong>{name}</strong>
          <pre>{JSON.stringify(liveData, null, 2)}</pre>
        </code>
      </Box>
    );
  };
  return (
    <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
      {caseWithLiveData('No Live Data', undefined)}
      {caseWithLiveData('Run Started - Not Materializing Yet', {
        stepKey: 'asset1',
        unstartedRunIds: ['ABCDEF'],
        inProgressRunIds: [],
        lastMaterialization: null,
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: null,
        currentLogicalVersion: null,
        projectedLogicalVersion: null,
        freshnessInfo: null,
        freshnessPolicy: null,
      })}
      {caseWithLiveData('Run Started - Materializing', {
        stepKey: 'asset1',
        unstartedRunIds: [],
        inProgressRunIds: ['ABCDEF'],
        lastMaterialization: null,
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: null,
        currentLogicalVersion: null,
        projectedLogicalVersion: null,
        freshnessInfo: null,
        freshnessPolicy: null,
      })}

      {caseWithLiveData('Run Failed to Materialize', {
        stepKey: 'asset1',
        unstartedRunIds: [],
        inProgressRunIds: [],
        lastMaterialization: null,
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: {
          __typename: 'Run',
          id: 'ABCDEF',
          status: RunStatus.FAILURE,
          endTime: 1673301346,
        },
        currentLogicalVersion: null,
        projectedLogicalVersion: null,
        freshnessInfo: null,
        freshnessPolicy: null,
      })}

      {caseWithLiveData('Never Materialized', {
        stepKey: 'asset1',
        unstartedRunIds: [],
        inProgressRunIds: [],
        lastMaterialization: null,
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: null,
        currentLogicalVersion: 'INITIAL',
        projectedLogicalVersion: 'V_A',
        freshnessInfo: null,
        freshnessPolicy: null,
      })}

      {caseWithLiveData('Materialized', {
        stepKey: 'asset1',
        unstartedRunIds: [],
        inProgressRunIds: [],
        lastMaterialization: {
          __typename: 'MaterializationEvent',
          runId: 'ABCDEF',
          timestamp: `${Date.now()}`,
        },
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: null,
        currentLogicalVersion: 'INITIAL',
        projectedLogicalVersion: 'V_A',
        freshnessInfo: null,
        freshnessPolicy: null,
      })}

      {caseWithLiveData('Materialized and Stale', {
        stepKey: 'asset1',
        unstartedRunIds: [],
        inProgressRunIds: [],
        lastMaterialization: {
          __typename: 'MaterializationEvent',
          runId: 'ABCDEF',
          timestamp: `${Date.now()}`,
        },
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: null,
        currentLogicalVersion: 'V_A',
        projectedLogicalVersion: 'V_B',
        freshnessInfo: null,
        freshnessPolicy: null,
      })}
      {caseWithLiveData('Materialized and Stale and Late', {
        stepKey: 'asset1',
        unstartedRunIds: [],
        inProgressRunIds: [],
        lastMaterialization: {
          __typename: 'MaterializationEvent',
          runId: 'ABCDEF',
          timestamp: `${Date.now()}`,
        },
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: null,
        currentLogicalVersion: 'V_A',
        projectedLogicalVersion: 'V_B',
        freshnessInfo: {
          __typename: 'AssetFreshnessInfo',
          currentMinutesLate: 12,
        },
        freshnessPolicy: {
          __typename: 'FreshnessPolicy',
          maximumLagMinutes: 10,
          cronSchedule: null,
        },
      })}
      {caseWithLiveData('Materialized and Stale and Fresh', {
        stepKey: 'asset1',
        unstartedRunIds: [],
        inProgressRunIds: [],
        lastMaterialization: {
          __typename: 'MaterializationEvent',
          runId: 'ABCDEF',
          timestamp: `${Date.now()}`,
        },
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: null,
        currentLogicalVersion: 'V_A',
        projectedLogicalVersion: 'V_B',
        freshnessInfo: {
          __typename: 'AssetFreshnessInfo',
          currentMinutesLate: 0,
        },
        freshnessPolicy: {
          __typename: 'FreshnessPolicy',
          maximumLagMinutes: 10,
          cronSchedule: null,
        },
      })}
      {caseWithLiveData('Materialized and Fresh', {
        stepKey: 'asset1',
        unstartedRunIds: [],
        inProgressRunIds: [],
        lastMaterialization: {
          __typename: 'MaterializationEvent',
          runId: 'ABCDEF',
          timestamp: `${Date.now()}`,
        },
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: null,
        currentLogicalVersion: 'V_B',
        projectedLogicalVersion: 'V_B',
        freshnessInfo: {
          __typename: 'AssetFreshnessInfo',
          currentMinutesLate: 0,
        },
        freshnessPolicy: {
          __typename: 'FreshnessPolicy',
          maximumLagMinutes: 10,
          cronSchedule: null,
        },
      })}
      {caseWithLiveData('Materialized and Late', {
        stepKey: 'asset1',
        unstartedRunIds: [],
        inProgressRunIds: [],
        lastMaterialization: {
          __typename: 'MaterializationEvent',
          runId: 'ABCDEF',
          timestamp: `${Date.now()}`,
        },
        lastMaterializationRunStatus: null,
        lastObservation: null,
        runWhichFailedToMaterialize: null,
        currentLogicalVersion: 'V_A',
        projectedLogicalVersion: 'V_A',
        freshnessInfo: {
          __typename: 'AssetFreshnessInfo',
          currentMinutesLate: 12,
        },
        freshnessPolicy: {
          __typename: 'FreshnessPolicy',
          maximumLagMinutes: 10,
          cronSchedule: null,
        },
      })}
      {caseWithLiveData('Source Asset - No Live Data', undefined, SOURCE_ASSET_NODE_DEFINITION)}

      {caseWithLiveData('Source Asset - Not Observable', undefined, {
        ...SOURCE_ASSET_NODE_DEFINITION,
        isObservable: false,
      })}

      {caseWithLiveData(
        'Source Asset - Never Observed',
        {
          stepKey: 'source_asset',
          unstartedRunIds: [],
          inProgressRunIds: [],
          lastMaterialization: null,
          lastMaterializationRunStatus: null,
          lastObservation: null,
          runWhichFailedToMaterialize: null,
          currentLogicalVersion: 'INITIAL',
          projectedLogicalVersion: null,
          freshnessInfo: null,
          freshnessPolicy: null,
        },
        SOURCE_ASSET_NODE_DEFINITION,
      )}

      {caseWithLiveData(
        'Source Asset - Observation Running',
        {
          stepKey: 'source_asset',
          unstartedRunIds: [],
          inProgressRunIds: ['12345'],
          lastMaterialization: null,
          lastMaterializationRunStatus: null,
          lastObservation: null,
          runWhichFailedToMaterialize: null,
          currentLogicalVersion: 'INITIAL',
          projectedLogicalVersion: null,
          freshnessInfo: null,
          freshnessPolicy: null,
        },
        SOURCE_ASSET_NODE_DEFINITION,
      )}

      {caseWithLiveData(
        'Source Asset - Observed, Stale',
        {
          stepKey: 'source_asset',
          unstartedRunIds: [],
          inProgressRunIds: ['12345'],
          lastMaterialization: null,
          lastMaterializationRunStatus: null,
          lastObservation: {
            __typename: 'ObservationEvent',
            runId: 'ABCDEF',
            timestamp: `${Date.now()}`,
          },
          runWhichFailedToMaterialize: null,
          currentLogicalVersion: 'INITIAL',
          projectedLogicalVersion: 'DIFFERENT',
          freshnessInfo: null,
          freshnessPolicy: null,
        },
        SOURCE_ASSET_NODE_DEFINITION,
      )}

      {caseWithLiveData(
        'Source Asset - Observed, Up To Date',
        {
          stepKey: 'source_asset',
          unstartedRunIds: [],
          inProgressRunIds: [],
          lastMaterialization: null,
          lastMaterializationRunStatus: null,
          lastObservation: {
            __typename: 'ObservationEvent',
            runId: 'ABCDEF',
            timestamp: `${Date.now()}`,
          },
          runWhichFailedToMaterialize: null,
          currentLogicalVersion: 'DIFFERENT',
          projectedLogicalVersion: 'DIFFERENT',
          freshnessInfo: null,
          freshnessPolicy: null,
        },
        SOURCE_ASSET_NODE_DEFINITION,
      )}
    </Box>
  );
  return;
};
