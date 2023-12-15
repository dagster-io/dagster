import {gql, useQuery} from '@apollo/client';
import 'chartjs-adapter-date-fns';
import {
  Button,
  DialogFooter,
  Dialog,
  Box,
  Subtitle2,
  Table,
  Spinner,
  DialogHeader,
  ButtonLink,
  Tag,
  MiddleTruncate,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {formatElapsedTimeWithoutMsec} from '../app/Util';
import {Timestamp} from '../app/time/Timestamp';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {
  DynamicPartitionsRequestResult,
  DynamicPartitionsRequestType,
  InstigationSelector,
  InstigationTickStatus,
} from '../graphql/types';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

import {FailedRunList, RunList} from './InstigationTick';
import {HISTORY_TICK_FRAGMENT} from './InstigationUtils';
import {HistoryTickFragment} from './types/InstigationUtils.types';
import {SelectedTickQuery, SelectedTickQueryVariables} from './types/TickDetailsDialog.types';

interface DialogProps extends InnerProps {
  onClose: () => void;
  isOpen: boolean;
}

export const TickDetailsDialog = ({tickId, isOpen, instigationSelector, onClose}: DialogProps) => {
  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      style={{width: '80vw', maxWidth: '1200px', minWidth: '600px'}}
    >
      <TickDetailsDialogImpl tickId={tickId} instigationSelector={instigationSelector} />
      <DialogFooter>
        <Button onClick={onClose}>Close</Button>
      </DialogFooter>
    </Dialog>
  );
};

interface InnerProps {
  tickId: number | undefined;
  instigationSelector: InstigationSelector;
}

const TickDetailsDialogImpl = ({tickId, instigationSelector}: InnerProps) => {
  const {data} = useQuery<SelectedTickQuery, SelectedTickQueryVariables>(JOB_SELECTED_TICK_QUERY, {
    variables: {instigationSelector, tickId: tickId || 0},
    skip: !tickId,
  });

  const tick =
    data?.instigationStateOrError.__typename === 'InstigationState'
      ? data?.instigationStateOrError.tick
      : undefined;

  const [addedPartitions, deletedPartitions] = React.useMemo(() => {
    const added = tick?.dynamicPartitionsRequestResults.filter(
      (request) =>
        request.type === DynamicPartitionsRequestType.ADD_PARTITIONS &&
        request.partitionKeys?.length,
    );
    const deleted = tick?.dynamicPartitionsRequestResults.filter(
      (request) =>
        request.type === DynamicPartitionsRequestType.DELETE_PARTITIONS &&
        request.partitionKeys?.length,
    );
    return [added, deleted];
  }, [tick?.dynamicPartitionsRequestResults]);

  if (!tick) {
    return (
      <Box style={{padding: 32}} flex={{alignItems: 'center', justifyContent: 'center'}}>
        <Spinner purpose="section" />
      </Box>
    );
  }

  return (
    <>
      <DialogHeader
        label={
          <TimestampDisplay
            timestamp={tick.timestamp}
            timeFormat={{showTimezone: false, showSeconds: true}}
          />
        }
      />
      <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
        <TickDetailSummary tick={tick} />
      </Box>
      {tick.runIds.length || tick.originRunIds.length ? (
        <>
          <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
            <Subtitle2>Runs requested</Subtitle2>
          </Box>
          {tick.runIds.length ? (
            <RunList runIds={tick.runIds} />
          ) : (
            <FailedRunList originRunIds={tick.originRunIds} />
          )}
        </>
      ) : null}
      {addedPartitions?.length ? (
        <>
          <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
            <Subtitle2>Added partitions</Subtitle2>
          </Box>
          <PartitionsTable partitions={addedPartitions} />
        </>
      ) : null}
      {deletedPartitions?.length ? (
        <>
          <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
            <Subtitle2>Deleted partitions</Subtitle2>
          </Box>
          <PartitionsTable partitions={deletedPartitions} />
        </>
      ) : null}
    </>
  );
};

export function TickDetailSummary({tick}: {tick: HistoryTickFragment | AssetDaemonTickFragment}) {
  const intent = React.useMemo(() => {
    switch (tick?.status) {
      case InstigationTickStatus.FAILURE:
        return 'danger';
      case InstigationTickStatus.STARTED:
        return 'primary';
      case InstigationTickStatus.SUCCESS:
        return 'success';
    }
    return undefined;
  }, [tick]);

  const isAssetDaemonTick = 'requestedAssetMaterializationCount' in tick;

  return (
    <>
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12}}>
        <Box flex={{direction: 'column', gap: 4}}>
          <Subtitle2>Status</Subtitle2>
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <Tag intent={intent}>
              {tick.status === InstigationTickStatus.STARTED ? (
                'Evaluating…'
              ) : (
                <>
                  {(isAssetDaemonTick
                    ? tick.requestedAssetMaterializationCount
                    : tick.runIds.length) ?? 0}{' '}
                  requested
                </>
              )}
            </Tag>
            {tick.error ? (
              <ButtonLink
                onClick={() => {
                  showCustomAlert({
                    title: 'Tick error',
                    body: <PythonErrorInfo error={tick.error!} />,
                  });
                }}
              >
                View error
              </ButtonLink>
            ) : null}
          </Box>
        </Box>
        <Box flex={{direction: 'column', gap: 4}}>
          <Subtitle2>Timestamp</Subtitle2>
          <div>
            {tick ? (
              <Timestamp timestamp={{unix: tick.timestamp}} timeFormat={{showTimezone: true}} />
            ) : (
              '–'
            )}
          </div>
        </Box>
        <Box flex={{direction: 'column', gap: 4}}>
          <Subtitle2>Duration</Subtitle2>
          <div>
            {tick?.endTimestamp
              ? formatElapsedTimeWithoutMsec(tick.endTimestamp * 1000 - tick.timestamp * 1000)
              : '\u2013'}
          </div>
        </Box>
      </div>
    </>
  );
}

function PartitionsTable({partitions}: {partitions: DynamicPartitionsRequestResult[]}) {
  return (
    <Table>
      <thead>
        <tr>
          <th>Partition definition</th>
          <th>Partition</th>
        </tr>
      </thead>
      <tbody>
        {partitions.flatMap(
          (partition) =>
            partition.partitionKeys?.map((key) => (
              <tr key={key}>
                <td>
                  <MiddleTruncate text={partition.partitionsDefName} />
                </td>
                <td>
                  <MiddleTruncate text={key} />
                </td>
              </tr>
            )),
        )}
      </tbody>
    </Table>
  );
}

const JOB_SELECTED_TICK_QUERY = gql`
  query SelectedTickQuery($instigationSelector: InstigationSelector!, $tickId: Int!) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      ... on InstigationState {
        id
        tick(tickId: $tickId) {
          id
          ...HistoryTick
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${HISTORY_TICK_FRAGMENT}
`;
