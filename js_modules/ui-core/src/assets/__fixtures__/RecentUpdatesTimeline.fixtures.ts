import {buildMaterializationEvent, buildObservationEvent} from '../../graphql/builders';
import {AssetEventFragment} from '../useRecentAssetEvents';

export const ONE_HOUR_MS = 60 * 60 * 1000;

// Fixed reference time the fixture timestamps are anchored to, so stories render
// deterministically regardless of when they're viewed: 2024-11-15T15:36:40Z.
export const FIXTURE_BASE_TIME = new Date('2024-11-15T15:36:40Z').getTime();

export const MultipleMaterializationEvents: AssetEventFragment[] = [
  buildMaterializationEvent({timestamp: '1731685015904'}),
  buildMaterializationEvent({timestamp: '1731685020904'}),
  buildMaterializationEvent({timestamp: '1731685032904'}),
  buildMaterializationEvent({timestamp: '1731685043904'}),
  buildMaterializationEvent({timestamp: '1731685044904'}),
  buildMaterializationEvent({timestamp: '1731685045904'}),
];

export const MixedMaterializationsAndObservationsEvents: AssetEventFragment[] = [
  buildMaterializationEvent({timestamp: `${FIXTURE_BASE_TIME}`}),
  buildObservationEvent({timestamp: `${FIXTURE_BASE_TIME + 1 * ONE_HOUR_MS}`}),
  buildMaterializationEvent({timestamp: `${FIXTURE_BASE_TIME + 2 * ONE_HOUR_MS}`}),
  buildObservationEvent({timestamp: `${FIXTURE_BASE_TIME + 3 * ONE_HOUR_MS}`}),
  buildObservationEvent({timestamp: `${FIXTURE_BASE_TIME + 4 * ONE_HOUR_MS}`}),
  buildMaterializationEvent({timestamp: `${FIXTURE_BASE_TIME + 5 * ONE_HOUR_MS}`}),
  buildObservationEvent({timestamp: `${FIXTURE_BASE_TIME + 6 * ONE_HOUR_MS}`}),
  buildMaterializationEvent({timestamp: `${FIXTURE_BASE_TIME + 7 * ONE_HOUR_MS}`}),
  buildMaterializationEvent({timestamp: `${FIXTURE_BASE_TIME + 8 * ONE_HOUR_MS}`}),
  buildObservationEvent({timestamp: `${FIXTURE_BASE_TIME + 9 * ONE_HOUR_MS}`}),
];
