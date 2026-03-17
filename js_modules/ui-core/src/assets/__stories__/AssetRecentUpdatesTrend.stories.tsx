import {
  buildAssetLatestInfo,
  buildFailedToMaterializeEvent,
  buildMaterializationEvent,
  buildObservationEvent,
  buildRun,
} from '../../graphql/builders';
import {RunStatus} from '../../graphql/types';
import {AssetRecentUpdatesTrend} from '../AssetRecentUpdatesTrend';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/AssetRecentUpdatesTrend',
  component: AssetRecentUpdatesTrend,
};

export const Empty = () => <AssetRecentUpdatesTrend events={[]} />;

export const AllMaterializations = () => (
  <AssetRecentUpdatesTrend
    events={[
      buildMaterializationEvent({runId: 'run-1', timestamp: '1731685010000'}),
      buildMaterializationEvent({runId: 'run-2', timestamp: '1731685020000'}),
      buildMaterializationEvent({runId: 'run-3', timestamp: '1731685030000'}),
      buildMaterializationEvent({runId: 'run-4', timestamp: '1731685040000'}),
      buildMaterializationEvent({runId: 'run-5', timestamp: '1731685050000'}),
    ]}
  />
);

export const MixedEventTypes = () => (
  <AssetRecentUpdatesTrend
    events={[
      buildMaterializationEvent({runId: 'run-1', timestamp: '1731685010000'}),
      buildObservationEvent({runId: 'run-2', timestamp: '1731685020000'}),
      buildFailedToMaterializeEvent({runId: 'run-3', timestamp: '1731685030000'}),
      buildMaterializationEvent({runId: 'run-4', timestamp: '1731685040000'}),
      buildObservationEvent({runId: 'run-5', timestamp: '1731685050000'}),
    ]}
  />
);

/**
 * This story exercises the duplicate React key bug: when a materialization and
 * observation (or failure) share the same runId, the component uses `event.runId`
 * as the key for both, producing duplicate keys.
 */
export const SharedRunIds = () => (
  <AssetRecentUpdatesTrend
    events={[
      buildMaterializationEvent({runId: 'shared-run-1', timestamp: '1731685010000'}),
      buildObservationEvent({runId: 'shared-run-1', timestamp: '1731685011000'}),
      buildMaterializationEvent({runId: 'shared-run-2', timestamp: '1731685020000'}),
      buildFailedToMaterializeEvent({runId: 'shared-run-2', timestamp: '1731685021000'}),
      buildMaterializationEvent({runId: 'run-3', timestamp: '1731685030000'}),
    ]}
  />
);

export const WithLatestInfo = () => (
  <AssetRecentUpdatesTrend
    latestInfo={buildAssetLatestInfo({
      latestRun: buildRun({
        id: 'latest-run',
        status: RunStatus.STARTED,
        startTime: 1731685060,
      }),
    })}
    events={[
      buildMaterializationEvent({runId: 'run-1', timestamp: '1731685010000'}),
      buildObservationEvent({runId: 'run-2', timestamp: '1731685020000'}),
      buildMaterializationEvent({runId: 'run-3', timestamp: '1731685030000'}),
      buildMaterializationEvent({runId: 'run-4', timestamp: '1731685040000'}),
    ]}
  />
);

export const PartiallyFilled = () => (
  <AssetRecentUpdatesTrend
    events={[
      buildMaterializationEvent({runId: 'run-1', timestamp: '1731685010000'}),
      buildObservationEvent({runId: 'run-2', timestamp: '1731685020000'}),
    ]}
  />
);
