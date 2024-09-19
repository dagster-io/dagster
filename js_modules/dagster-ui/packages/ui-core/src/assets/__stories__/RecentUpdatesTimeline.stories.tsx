import {buildAssetKey, buildMaterializationEvent} from '../../graphql/types';
import {PartitionHealthSummary} from '../PartitionHealthSummary';
import {RecentUpdatesTimeline} from '../RecentUpdatesTimeline';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/RecentUpdatesTimeline',
  component: PartitionHealthSummary,
};

export const Single = () => (
  <RecentUpdatesTimeline
    assetKey={buildAssetKey()}
    loading={false}
    materializations={[buildMaterializationEvent({timestamp: '1'})]}
  />
);

export const Multiple = () => (
  <RecentUpdatesTimeline
    assetKey={buildAssetKey()}
    loading={false}
    materializations={[
      buildMaterializationEvent({
        timestamp: '1',
      }),
      buildMaterializationEvent({
        timestamp: '2',
      }),
      buildMaterializationEvent({
        timestamp: '4',
      }),
      buildMaterializationEvent({
        timestamp: '5',
      }),
      buildMaterializationEvent({
        timestamp: '9',
      }),
      buildMaterializationEvent({
        timestamp: '12',
      }),
    ]}
  />
);
