import {buildAssetKey, buildMaterializationEvent} from '../../graphql/types';
import {PartitionHealthSummary} from '../PartitionHealthSummary';
import {RecentUpdatesTimeline} from '../RecentUpdatesTimeline';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/RecentUpdatesTimeline',
  component: PartitionHealthSummary,
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
