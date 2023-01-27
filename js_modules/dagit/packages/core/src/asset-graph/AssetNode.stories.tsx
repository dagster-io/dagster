import {Box} from '@dagster-io/ui';
import React from 'react';

import {KNOWN_TAGS} from '../graph/OpTags';

import {AssetNode, AssetNodeMinimal} from './AssetNode';
import * as Mocks from './AssetNode.mocks';
import {LiveDataForNode} from './Utils';
import {getAssetNodeDimensions} from './layout';
import {AssetNodeFragment} from './types/AssetNode.types';

// eslint-disable-next-line import/no-default-export
export default {component: AssetNode};

export const LiveStates = () => {
  const caseWithLiveData = (
    name: string,
    liveData: LiveDataForNode | undefined = undefined,
    def: AssetNodeFragment = Mocks.AssetNodeFragmentBasic,
  ) => {
    const dimensions = getAssetNodeDimensions(def);
    return (
      <Box flex={{direction: 'column', gap: 0, alignItems: 'flex-start'}}>
        <div
          style={{position: 'relative', width: 280, height: dimensions.height, overflowY: 'hidden'}}
        >
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
    <>
      <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
        {caseWithLiveData('No Live Data', undefined)}

        {caseWithLiveData(
          'Run Started - Not Materializing Yet',
          Mocks.LiveDataForNodeRunStartedNotMaterializing,
        )}
        {caseWithLiveData(
          'Run Started - Materializing',
          Mocks.LiveDataForNodeRunStartedMaterializing,
        )}

        {caseWithLiveData('Run Failed to Materialize', Mocks.LiveDataForNodeRunFailed)}

        {caseWithLiveData('Never Materialized', Mocks.LiveDataForNodeNeverMaterialized)}

        {caseWithLiveData('Materialized', Mocks.LiveDataForNodeMaterialized)}

        {caseWithLiveData('Materialized and Stale', Mocks.LiveDataForNodeMaterializedAndStale)}

        {caseWithLiveData(
          'Materialized and Stale and Late',
          Mocks.LiveDataForNodeMaterializedAndStaleAndLate,
        )}

        {caseWithLiveData(
          'Materialized and Stale and Fresh',
          Mocks.LiveDataForNodeMaterializedAndStaleAndFresh,
        )}

        {caseWithLiveData('Materialized and Fresh', Mocks.LiveDataForNodeMaterializedAndFresh)}

        {caseWithLiveData('Materialized and Late', Mocks.LiveDataForNodeMaterializedAndLate)}
      </Box>

      <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
        {caseWithLiveData('Source Asset - No Live Data', undefined, Mocks.AssetNodeFragmentSource)}

        {caseWithLiveData('Source Asset - Not Observable', undefined, {
          ...Mocks.AssetNodeFragmentSource,
          isObservable: false,
        })}

        {caseWithLiveData('Source Asset - Not Observable, No Description', undefined, {
          ...Mocks.AssetNodeFragmentSource,
          isObservable: false,
          description: null,
        })}

        {caseWithLiveData(
          'Source Asset - Never Observed',
          Mocks.LiveDataForNodeSourceNeverObserved,
          Mocks.AssetNodeFragmentSource,
        )}

        {caseWithLiveData(
          'Source Asset - Observation Running',
          Mocks.LiveDataForNodeSourceObservationRunning,
          Mocks.AssetNodeFragmentSource,
        )}

        {caseWithLiveData(
          'Source Asset - Observed, Stale',
          Mocks.LiveDataForNodeSourceObservedStale,
          Mocks.AssetNodeFragmentSource,
        )}

        {caseWithLiveData(
          'Source Asset - Observed, Up To Date',
          Mocks.LiveDataForNodeSourceObservedUpToDate,
          Mocks.AssetNodeFragmentSource,
        )}
      </Box>
      <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
        {caseWithLiveData(
          'Partitioned Asset - Some Missing',
          Mocks.LiveDataForNodePartitionedSomeMissing,
          Mocks.AssetNodeFragmentPartitioned,
        )}

        {caseWithLiveData(
          'Partitioned Asset - None Missing',
          Mocks.LiveDataForNodePartitionedNoneMissing,
          Mocks.AssetNodeFragmentPartitioned,
        )}

        {caseWithLiveData(
          'Never Materialized',
          Mocks.LiveDataForNodePartitionedNeverMaterialized,
          Mocks.AssetNodeFragmentPartitioned,
        )}

        {caseWithLiveData(
          'Partitioned Asset - Stale',
          Mocks.LiveDataForNodePartitionedStale,
          Mocks.AssetNodeFragmentPartitioned,
        )}

        {caseWithLiveData(
          'Partitioned Asset - Stale and Late',
          Mocks.LiveDataForNodePartitionedStaleAndLate,
          Mocks.AssetNodeFragmentPartitioned,
        )}

        {caseWithLiveData(
          'Partitioned Asset - Stale and Fresh',
          Mocks.LiveDataForNodePartitionedStaleAndFresh,
          Mocks.AssetNodeFragmentPartitioned,
        )}

        {caseWithLiveData(
          'Partitioned Asset - Last Run Failed',
          Mocks.LiveDataForNodePartitionedLatestRunFailed,
          Mocks.AssetNodeFragmentPartitioned,
        )}
      </Box>
    </>
  );
  return;
};

export const PartnerTags = () => {
  const caseWithComputeKind = (computeKind: string) => {
    const def = {...Mocks.AssetNodeFragmentBasic, computeKind};
    const liveData = Mocks.LiveDataForNodeMaterialized;
    const dimensions = getAssetNodeDimensions(def);

    return (
      <Box flex={{direction: 'column', gap: 0, alignItems: 'flex-start'}}>
        <strong>{computeKind}</strong>
        <div
          style={{position: 'relative', width: 280, height: dimensions.height, overflowY: 'hidden'}}
        >
          <AssetNode definition={def} selected={false} liveData={liveData} />
        </div>
      </Box>
    );
  };

  return (
    <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
      {Object.keys(KNOWN_TAGS).map(caseWithComputeKind)}
      {caseWithComputeKind('Unknown-Kind-Long')}
      {caseWithComputeKind('another')}
    </Box>
  );
};
