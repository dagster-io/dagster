import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogFooter,
  ExternalAnchorButton,
  Icon,
  NonIdealState,
  SpinnerWithText,
} from '@dagster-io/ui-components';

import {INSTIGATION_EVENT_LOG_FRAGMENT, InstigationEventLogTable} from './InstigationEventLogTable';
import {gql, useQuery} from '../apollo-client';
import {TickLogEventsQuery, TickLogEventsQueryVariables} from './types/TickLogDialog.types';
import {InstigationSelector} from '../graphql/types';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

export const TickLogDialog = ({
  tickId,
  timestamp,
  instigationSelector,
  isOpen,
  onClose,
}: {
  tickId: string | null;
  timestamp?: number;
  instigationSelector: InstigationSelector;
  isOpen: boolean;
  onClose: () => void;
}) => {
  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      style={{width: '70vw', maxWidth: '1200px', minWidth: '800px'}}
      title={
        <span>
          {timestamp ? (
            <span>
              <span>Logs for {instigationSelector.name}: </span>
              <TimestampDisplay timestamp={timestamp} timeFormat={{showSeconds: true}} />
            </span>
          ) : (
            <span>Logs for {instigationSelector.name}</span>
          )}
        </span>
      }
    >
      {tickId ? (
        <QueryfulTickLogsTable instigationSelector={instigationSelector} tickId={tickId} />
      ) : null}
      {/* Use z-index to force the footer to sit above the lines of the logs table */}
      <Box background={Colors.backgroundDefault()} style={{zIndex: 3, position: 'relative'}}>
        <DialogFooter topBorder>
          <Button onClick={onClose}>Done</Button>
        </DialogFooter>
      </Box>
    </Dialog>
  );
};

interface TickLogTableProps {
  tickId: string;
  instigationSelector: InstigationSelector;
}

export const QueryfulTickLogsTable = ({instigationSelector, tickId}: TickLogTableProps) => {
  const {data, loading} = useQuery<TickLogEventsQuery, TickLogEventsQueryVariables>(
    TICK_LOG_EVENTS_QUERY,
    {
      variables: {instigationSelector, tickId},
      notifyOnNetworkStatusChange: true,
    },
  );

  const events =
    data?.instigationStateOrError.__typename === 'InstigationState' &&
    data?.instigationStateOrError.tick
      ? data?.instigationStateOrError.tick.logEvents.events
      : undefined;

  if (loading) {
    return (
      <Box style={{height: 500}} flex={{justifyContent: 'center', alignItems: 'center'}}>
        <SpinnerWithText label="Loading logs…" />
      </Box>
    );
  }

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
    </Box>
  );
};

const TICK_LOG_EVENTS_QUERY = gql`
  query TickLogEventsQuery($instigationSelector: InstigationSelector!, $tickId: ID!) {
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
