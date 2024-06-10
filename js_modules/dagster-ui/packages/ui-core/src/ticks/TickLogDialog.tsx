import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  ExternalAnchorButton,
  Icon,
  NonIdealState,
} from '@dagster-io/ui-components';

import {INSTIGATION_EVENT_LOG_FRAGMENT, InstigationEventLogTable} from './InstigationEventLogTable';
import {TickLogEventsQuery, TickLogEventsQueryVariables} from './types/TickLogDialog.types';
import {InstigationSelector} from '../graphql/types';
import {HistoryTickFragment} from '../instigation/types/InstigationUtils.types';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

export const TickLogDialog = ({
  tick,
  instigationSelector,
  onClose,
}: {
  tick: HistoryTickFragment;
  instigationSelector: InstigationSelector;
  onClose: () => void;
}) => {
  const {data} = useQuery<TickLogEventsQuery, TickLogEventsQueryVariables>(TICK_LOG_EVENTS_QUERY, {
    variables: {instigationSelector, tickId: Number(tick.tickId)},
    notifyOnNetworkStatusChange: true,
  });

  const events =
    data?.instigationStateOrError.__typename === 'InstigationState' &&
    data?.instigationStateOrError.tick
      ? data?.instigationStateOrError.tick.logEvents.events
      : undefined;

  return (
    <Dialog
      isOpen={!!events}
      onClose={onClose}
      style={{width: '70vw', display: 'flex'}}
      title={tick ? <TimestampDisplay timestamp={tick.timestamp} /> : null}
    >
      <DialogBody>
        {events && events.length ? (
          <InstigationEventLogTable events={events} />
        ) : (
          <Box
            flex={{justifyContent: 'center', alignItems: 'center'}}
            style={{flex: 1, color: Colors.textLight()}}
          >
            No logs available
          </Box>
        )}
      </DialogBody>
      <DialogFooter>
        <Button intent="primary" onClick={onClose}>
          OK
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

interface TickLogTableProps {
  tick: HistoryTickFragment;
  instigationSelector: InstigationSelector;
}

export const QueryfulTickLogsTable = ({instigationSelector, tick}: TickLogTableProps) => {
  const {data, loading} = useQuery<TickLogEventsQuery, TickLogEventsQueryVariables>(
    TICK_LOG_EVENTS_QUERY,
    {
      variables: {instigationSelector, tickId: Number(tick.tickId)},
    },
  );

  const events =
    data?.instigationStateOrError.__typename === 'InstigationState' &&
    data?.instigationStateOrError.tick
      ? data?.instigationStateOrError.tick.logEvents.events
      : undefined;

  if (events && events.length) {
    return (
      <Box style={{height: 500}} flex={{direction: 'column'}}>
        <InstigationEventLogTable events={events} />
      </Box>
    );
  }

  const tickStatus =
    data?.instigationStateOrError.__typename === 'InstigationState'
      ? data?.instigationStateOrError.tick.status
      : undefined;
  const instigationType =
    data?.instigationStateOrError.__typename === 'InstigationState'
      ? data?.instigationStateOrError.instigationType
      : undefined;
  const instigationLoggingDocsUrl =
    instigationType === 'SENSOR'
      ? 'https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#logging-in-sensors'
      : instigationType === 'SCHEDULE'
      ? 'https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules#logging-in-schedules'
      : undefined;

  return (
    <Box
      style={{height: 500}}
      flex={{justifyContent: 'center', alignItems: 'center'}}
      padding={{vertical: 48}}
    >
      {loading ? (
        'Loading logs…'
      ) : (
        <NonIdealState
          icon="no-results"
          title="No logs to display"
          description={
            <Box flex={{direction: 'column', gap: 12}}>
              <div>
                Your evaluation did not emit any logs. To learn how to emit logs in your evaluation,
                visit the documentation for more information.
              </div>
              {tickStatus === 'FAILURE' && (
                <>
                  <div>
                    For failed evaluations, logs will only be displayed if your Dagster and Dagster
                    Cloud agent versions 1.5.14 or higher.
                  </div>
                  <div>Upgrade your Dagster versions to view logs for failed evaluations.</div>
                </>
              )}
            </Box>
          }
          action={
            instigationLoggingDocsUrl && (
              <ExternalAnchorButton
                href={instigationLoggingDocsUrl}
                rightIcon={<Icon name="open_in_new" />}
              >
                View documentation
              </ExternalAnchorButton>
            )
          }
        />
      )}
    </Box>
  );
};

const TICK_LOG_EVENTS_QUERY = gql`
  query TickLogEventsQuery($instigationSelector: InstigationSelector!, $tickId: BigInt!) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      ... on InstigationState {
        id
        instigationType
        tick(tickId: $tickId) {
          id
          status
          timestamp
          logEvents {
            events {
              ...InstigationEventLog
            }
          }
        }
      }
    }
  }
  ${INSTIGATION_EVENT_LOG_FRAGMENT}
`;
