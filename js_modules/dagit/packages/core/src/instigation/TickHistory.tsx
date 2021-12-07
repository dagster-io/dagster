import {gql, useQuery} from '@apollo/client';
import {Chart} from 'chart.js';
import 'chartjs-adapter-date-fns';
import zoomPlugin from 'chartjs-plugin-zoom';
import * as React from 'react';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {InstigationTickStatus, InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {Checkbox} from '../ui/Checkbox';
import {ColorsWIP} from '../ui/Colors';
import {NonIdealState} from '../ui/NonIdealState';
import {Spinner} from '../ui/Spinner';
import {Tab, Tabs} from '../ui/Tabs';
import {Subheading} from '../ui/Text';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {HistoricalTickTimeline} from './HistoricalTickTimeline';
import {TICK_TAG_FRAGMENT} from './InstigationTick';
import {LiveTickTimeline} from './LiveTickTimeline';
import {TickDetailsDialog} from './TickDetailsDialog';
import {
  TickHistoryQuery,
  TickHistoryQueryVariables,
  TickHistoryQuery_instigationStateOrError_InstigationState_ticks,
} from './types/TickHistoryQuery';

Chart.register(zoomPlugin);

type InstigationTick = TickHistoryQuery_instigationStateOrError_InstigationState_ticks;

interface ShownStatusState {
  [InstigationTickStatus.SUCCESS]: boolean;
  [InstigationTickStatus.FAILURE]: boolean;
  [InstigationTickStatus.STARTED]: boolean;
  [InstigationTickStatus.SKIPPED]: boolean;
}

const DEFAULT_SHOWN_STATUS_STATE = {
  [InstigationTickStatus.SUCCESS]: true,
  [InstigationTickStatus.FAILURE]: true,
  [InstigationTickStatus.STARTED]: true,
  [InstigationTickStatus.SKIPPED]: true,
};
const STATUS_TEXT_MAP = {
  [InstigationTickStatus.SUCCESS]: 'Requested',
  [InstigationTickStatus.FAILURE]: 'Failed',
  [InstigationTickStatus.STARTED]: 'Started',
  [InstigationTickStatus.SKIPPED]: 'Skipped',
};

const TABS = [
  {
    id: 'recent',
    label: 'Recent',
    range: 1,
  },
  {
    id: '1d',
    label: '1 day',
    range: 1,
  },
  {
    id: '7d',
    label: '7 days',
    range: 7,
  },
  {
    id: '14d',
    label: '14 days',
    range: 14,
  },
  {
    id: '30d',
    label: '30 days',
    range: 30,
  },
  {id: 'all', label: 'All'},
];

const MILLIS_PER_DAY = 86400 * 1000;

export const TickHistory = ({
  name,
  repoAddress,
  onHighlightRunIds,
  showRecent,
}: {
  name: string;
  repoAddress: RepoAddress;
  onHighlightRunIds: (runIds: string[]) => void;
  showRecent?: boolean;
}) => {
  const [selectedTab, setSelectedTab] = useQueryPersistedState<string>({
    queryKey: 'tab',
    defaults: {tab: 'recent'},
  });
  const [selectedTime, setSelectedTime] = useQueryPersistedState<number | undefined>({
    encode: (timestamp) => ({time: timestamp}),
    decode: (qs) => (qs['time'] ? Number(qs['time']) : undefined),
  });

  const [shownStates, setShownStates] = React.useState<ShownStatusState>(
    DEFAULT_SHOWN_STATUS_STATE,
  );
  const [pollingPaused, pausePolling] = React.useState<boolean>(false);

  React.useEffect(() => {
    if (!showRecent && selectedTab === 'recent') {
      setSelectedTab('1d');
    }
  }, [setSelectedTab, selectedTab, showRecent]);

  const instigationSelector = {...repoAddressToSelector(repoAddress), name};
  const selectedRange = TABS.find((x) => x.id === selectedTab)?.range;
  const {data} = useQuery<TickHistoryQuery, TickHistoryQueryVariables>(JOB_TICK_HISTORY_QUERY, {
    variables: {
      instigationSelector,
      dayRange: selectedRange,
      limit: selectedTab === 'recent' ? 15 : undefined,
    },
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    pollInterval: selectedTab === 'recent' && !pollingPaused ? 1000 : 0,
  });

  const tabs = (
    <Tabs selectedTabId={selectedTab} onChange={setSelectedTab}>
      {TABS.map((tab) =>
        tab.id === 'recent' && !showRecent ? null : (
          <Tab id={tab.id} key={tab.id} title={tab.label} />
        ),
      ).filter(Boolean)}
    </Tabs>
  );

  if (!data) {
    return (
      <>
        <Box
          padding={{top: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
        >
          <Subheading>Tick History</Subheading>
          {tabs}
        </Box>
        <Box padding={{vertical: 64}}>
          <Spinner purpose="section" />
        </Box>
      </>
    );
  }

  if (data.instigationStateOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={data.instigationStateOrError} />;
  }

  const {ticks, nextTick, instigationType} = data.instigationStateOrError;
  const displayedTicks = ticks.filter((tick) =>
    tick.status === InstigationTickStatus.SKIPPED
      ? instigationType === InstigationType.SCHEDULE && shownStates[tick.status]
      : shownStates[tick.status],
  );
  const StatusFilter = ({status}: {status: InstigationTickStatus}) => (
    <Checkbox
      label={STATUS_TEXT_MAP[status]}
      checked={shownStates[status]}
      disabled={!ticks.filter((tick) => tick.status === status).length}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
        setShownStates({...shownStates, [status]: e.target.checked});
      }}
    />
  );
  const onTickClick = (tick?: InstigationTick) => {
    setSelectedTime(tick ? tick.timestamp : undefined);
  };
  const onTickHover = (tick?: InstigationTick) => {
    if (!tick) {
      pausePolling(false);
    }
    if (tick?.runIds) {
      onHighlightRunIds(tick.runIds);
      pausePolling(true);
    }
  };

  const now = Date.now();

  return (
    <>
      <TickDetailsDialog
        timestamp={selectedTime}
        instigationSelector={instigationSelector}
        onClose={() => onTickClick(undefined)}
      />
      <Box padding={{top: 16, horizontal: 24}}>
        <Subheading>Tick History</Subheading>
        <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
          {tabs}
          {ticks.length ? (
            <Box flex={{direction: 'row', gap: 16}}>
              <StatusFilter status={InstigationTickStatus.SUCCESS} />
              <StatusFilter status={InstigationTickStatus.FAILURE} />
              {instigationType === InstigationType.SCHEDULE ? (
                <StatusFilter status={InstigationTickStatus.SKIPPED} />
              ) : null}
            </Box>
          ) : null}
        </Box>
      </Box>
      <Box padding={{bottom: 16}} border={{side: 'top', width: 1, color: ColorsWIP.KeylineGray}}>
        {showRecent && selectedTab === 'recent' ? (
          <LiveTickTimeline
            ticks={ticks}
            nextTick={nextTick}
            onHoverTick={onTickHover}
            onSelectTick={onTickClick}
          />
        ) : ticks.length ? (
          <HistoricalTickTimeline
            ticks={displayedTicks}
            selectedTick={displayedTicks.find((t) => t.timestamp === selectedTime)}
            onSelectTick={onTickClick}
            onHoverTick={onTickHover}
            selectedTab={selectedTab}
            maxBounds={
              selectedTab === 'all'
                ? undefined
                : {min: now - (selectedRange || 0) * MILLIS_PER_DAY, max: Date.now()}
            }
          />
        ) : (
          <Box padding={{vertical: 32}} flex={{justifyContent: 'center'}}>
            <NonIdealState
              icon="no-results"
              title="No ticks to display"
              description="There are no ticks within this timeframe."
            />
          </Box>
        )}
      </Box>
    </>
  );
};

const JOB_TICK_HISTORY_QUERY = gql`
  query TickHistoryQuery($instigationSelector: InstigationSelector!, $dayRange: Int, $limit: Int) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      __typename
      ... on InstigationState {
        id
        instigationType
        nextTick {
          timestamp
        }
        ticks(dayRange: $dayRange, limit: $limit) {
          id
          status
          timestamp
          skipReason
          runIds
          originRunIds
          error {
            ...PythonErrorFragment
          }
          ...TickTagFragment
        }
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
`;
