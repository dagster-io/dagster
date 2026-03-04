import {
  buildAssetKey,
  buildMaterializationEvent,
  buildObservationEvent,
} from '../../graphql/builders';
import {RecentUpdatesTimeline} from '../RecentUpdatesTimeline';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/RecentUpdatesTimeline',
  component: RecentUpdatesTimeline,
};

export const Loading = () => (
  <RecentUpdatesTimeline assetKey={buildAssetKey()} loading={true} events={undefined} />
);

export const Empty = () => (
  <RecentUpdatesTimeline assetKey={buildAssetKey()} loading={false} events={[]} />
);

export const Single = () => (
  <RecentUpdatesTimeline
    assetKey={buildAssetKey()}
    loading={false}
    events={[buildMaterializationEvent({timestamp: '1731685045904'})]}
  />
);

export const Multiple = () => (
  <RecentUpdatesTimeline
    assetKey={buildAssetKey()}
    loading={false}
    events={[
      buildMaterializationEvent({
        timestamp: '1731685015904',
      }),
      buildMaterializationEvent({
        timestamp: '1731685020904',
      }),
      buildMaterializationEvent({
        timestamp: '1731685032904',
      }),
      buildMaterializationEvent({
        timestamp: '1731685043904',
      }),
      buildMaterializationEvent({
        timestamp: '1731685044904',
      }),
      buildMaterializationEvent({
        timestamp: '1731685045904',
      }),
    ]}
  />
);

// Interleaved materializations and observations — triggers the filter toggle
export const MixedMaterializationsAndObservations = () => (
  <RecentUpdatesTimeline
    assetKey={buildAssetKey()}
    loading={false}
    events={[
      buildMaterializationEvent({timestamp: '1731685000000'}),
      buildObservationEvent({timestamp: '1731685005000'}),
      buildMaterializationEvent({timestamp: '1731685010000'}),
      buildObservationEvent({timestamp: '1731685015000'}),
      buildObservationEvent({timestamp: '1731685020000'}),
      buildMaterializationEvent({timestamp: '1731685025000'}),
      buildObservationEvent({timestamp: '1731685030000'}),
      buildMaterializationEvent({timestamp: '1731685035000'}),
      buildMaterializationEvent({timestamp: '1731685040000'}),
      buildObservationEvent({timestamp: '1731685045000'}),
    ]}
  />
);
