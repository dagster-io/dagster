import {useMemo, useState} from 'react';

import {
  buildAssetKey,
  buildFailedToMaterializeEvent,
  buildMaterializationEvent,
} from '../../graphql/builders';
import {
  RecentUpdatesTimelineView,
  RecentUpdatesTimelineViewProps,
  TimeRangeFilter,
} from '../RecentUpdatesTimeline';
import {
  FIXTURE_BASE_TIME,
  MixedMaterializationsAndObservationsEvents,
  MultipleMaterializationEvents,
  ONE_HOUR_MS,
} from '../__fixtures__/RecentUpdatesTimeline.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/RecentUpdatesTimeline',
  component: RecentUpdatesTimelineView,
};

type Events = RecentUpdatesTimelineViewProps['events'];

const TimelineStoryWrapper = ({events, now}: {events: Events; now?: number}) => {
  const [timeRange, setTimeRange] = useState<TimeRangeFilter>('24h');
  const [eventFilter, setEventFilter] =
    useState<RecentUpdatesTimelineViewProps['eventFilter']>('all');
  return (
    <RecentUpdatesTimelineView
      assetKey={buildAssetKey()}
      events={events}
      timeRange={timeRange}
      setTimeRange={setTimeRange}
      eventFilter={eventFilter}
      setEventFilter={setEventFilter}
      now={now}
    />
  );
};

// Anchor the timeline's "now" so fixture timestamps spread across the bar.
const STORY_NOW = FIXTURE_BASE_TIME + 10 * ONE_HOUR_MS;

export const Loading = () => <TimelineStoryWrapper events={null} now={STORY_NOW} />;

export const Empty = () => <TimelineStoryWrapper events={[]} now={STORY_NOW} />;

export const Multiple = () => (
  <TimelineStoryWrapper events={MultipleMaterializationEvents} now={STORY_NOW} />
);

// Interactive story: drag the slider to spread three materializations apart in time.
// At low spread values they group into a single "3" batch; as spread increases they
// separate into individual ticks. Use this to explore the grouping threshold.
export const GroupingExplorer = () => {
  const [spreadMinutes, setSpreadMinutes] = useState(0);
  const spreadMs = spreadMinutes * 60 * 1000;
  const center = FIXTURE_BASE_TIME + 5 * ONE_HOUR_MS;

  const events = useMemo(
    () => [
      buildMaterializationEvent({timestamp: `${FIXTURE_BASE_TIME}`}),
      buildMaterializationEvent({timestamp: `${center - spreadMs}`}),
      buildMaterializationEvent({timestamp: `${center}`}),
      buildMaterializationEvent({timestamp: `${center + spreadMs}`}),
    ],
    [center, spreadMs],
  );

  return (
    <div>
      <div style={{marginBottom: 12}}>
        <label>
          Spread between events:{' '}
          <strong>
            {spreadMinutes < 1
              ? `${Math.round(spreadMinutes * 60)}s`
              : `${spreadMinutes.toFixed(1)} min`}
          </strong>
          <br />
          <input
            type="range"
            min={0}
            max={60}
            step={0.1}
            value={spreadMinutes}
            onChange={(e) => setSpreadMinutes(Number(e.target.value))}
            style={{width: '100%', marginTop: 4}}
          />
        </label>
      </div>
      <TimelineStoryWrapper events={events} now={STORY_NOW} />
    </div>
  );
};

// 2 materializations + 1 failure within 500ms of each other — triggers grouping with mixed color.
// One isolated event 1 hour earlier creates a wide time range so the cluster collapses.
export const GroupedTwoSuccessesOneFailed = () => (
  <TimelineStoryWrapper
    now={STORY_NOW}
    events={[
      buildMaterializationEvent({timestamp: '1731685000000'}),
      buildMaterializationEvent({timestamp: '1731688600000'}),
      buildMaterializationEvent({timestamp: '1731688600200'}),
      buildFailedToMaterializeEvent({timestamp: '1731688600500'}),
    ]}
  />
);

// Interleaved materializations and observations — triggers the filter toggle
export const MixedMaterializationsAndObservations = () => (
  <TimelineStoryWrapper events={MixedMaterializationsAndObservationsEvents} now={STORY_NOW} />
);
