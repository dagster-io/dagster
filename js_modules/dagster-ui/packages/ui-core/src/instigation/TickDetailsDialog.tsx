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
  DialogBody,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {formatElapsedTime} from '../app/Util';
import {Timestamp} from '../app/time/Timestamp';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {
  DynamicPartitionsRequestResult,
  DynamicPartitionsRequestType,
  InstigationSelector,
  InstigationTickStatus,
} from '../graphql/types';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

import {FailedRunList, RunList, TICK_TAG_FRAGMENT} from './InstigationTick';
import {HISTORY_TICK_FRAGMENT} from './InstigationUtils';
import {HistoryTickFragment} from './types/InstigationUtils.types';
import {SelectedTickQuery, SelectedTickQueryVariables} from './types/TickDetailsDialog.types';

type Props = {
  timestamp: number | undefined;
  instigationSelector: InstigationSelector;
  onClose: () => void;
  isOpen: boolean;
};

export const TickDetailsDialog: React.FC<Props> = ({
  timestamp,
  isOpen,
  instigationSelector,
  onClose,
}) => {
  return (
    <Dialog isOpen={isOpen} onClose={onClose} style={{width: '90vw'}}>
      <TickDetailsDialogImpl timestamp={timestamp} instigationSelector={instigationSelector} />
      <DialogFooter>
        <Button onClick={onClose}>Close</Button>
      </DialogFooter>
    </Dialog>
  );
};

const TickDetailsDialogImpl = ({
  timestamp,
  instigationSelector,
}: Omit<Props, 'isOpen' | 'onClose'>) => {
  const {data} = useQuery<SelectedTickQuery, SelectedTickQueryVariables>(JOB_SELECTED_TICK_QUERY, {
    variables: {instigationSelector, timestamp: timestamp || 0},
    skip: !timestamp,
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
    return <Spinner purpose="section" />;
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
  const [showPythonError, setShowPythonError] = React.useState<PythonErrorFragment | null>(null);

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
      {showPythonError ? (
        <Dialog
          title="Error"
          isOpen={!!showPythonError}
          onClose={() => {
            setShowPythonError(null);
          }}
          style={{width: '80vw'}}
        >
          <DialogBody>
            <PythonErrorInfo error={showPythonError} />
          </DialogBody>
          <DialogFooter topBorder>
            <Button
              intent="primary"
              onClick={() => {
                setShowPythonError(null);
              }}
            >
              Close
            </Button>
          </DialogFooter>
        </Dialog>
      ) : null}
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
                  setShowPythonError(tick.error!);
                }}
              >
                View error
              </ButtonLink>
            ) : null}
          </Box>
        </Box>
        <Box flex={{direction: 'column', gap: 4}}>
          <Subtitle2>Timestamp</Subtitle2>
          <div>{tick ? <Timestamp timestamp={{unix: tick.timestamp}} /> : '–'}</div>
        </Box>
        <Box flex={{direction: 'column', gap: 4}}>
          <Subtitle2>Duration</Subtitle2>
          <div>
            {tick?.endTimestamp
              ? formatElapsedTime(tick.endTimestamp * 1000 - tick.timestamp * 1000)
              : '–'}
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
          <th>Asset</th>
          <th>Partition</th>
        </tr>
      </thead>
      <tbody>
        {partitions.flatMap(
          (partition) =>
            partition.partitionKeys?.map((key) => (
              <tr key={key}>
                <td>{partition.partitionsDefName}</td>
                <td>{key}</td>
              </tr>
            )),
        )}
      </tbody>
    </Table>
  );
}

const JOB_SELECTED_TICK_QUERY = gql`
  query SelectedTickQuery($instigationSelector: InstigationSelector!, $timestamp: Float!) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      ... on InstigationState {
        id
        tick(timestamp: $timestamp) {
          id
          ...HistoryTick
          ...TickTagFragment
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
  ${HISTORY_TICK_FRAGMENT}
`;
