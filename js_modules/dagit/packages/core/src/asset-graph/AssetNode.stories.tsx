import {Box} from '@dagster-io/ui';
import React from 'react';

import {RunStatus} from '../types/globalTypes';

import {AssetNode, AssetNodeMinimal} from './AssetNode';
import {LiveDataForNode} from './Utils';
import {AssetNodeFragment} from './types/AssetNodeFragment';

const ASSET_NODE_DEFINITION: AssetNodeFragment = {
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

// eslint-disable-next-line import/no-default-export
export default {component: AssetNode};

export const LiveStates = () => {
  const caseWithLiveData = (name: string, liveData?: LiveDataForNode) => {
    return (
      <Box flex={{direction: 'column', gap: 0, alignItems: 'flex-start'}}>
        <div style={{position: 'relative', width: 280}}>
          <AssetNode definition={ASSET_NODE_DEFINITION} selected={false} liveData={liveData} />
        </div>
        <div style={{position: 'relative', width: 280, height: 82}}>
          <div style={{position: 'absolute', width: 280, height: 82}}>
            <AssetNodeMinimal
              definition={ASSET_NODE_DEFINITION}
              selected={false}
              liveData={liveData}
            />
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
        runWhichFailedToMaterialize: {__typename: 'Run', id: 'ABCDEF', status: RunStatus.FAILURE},
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
    </Box>
  );
  return;
};
