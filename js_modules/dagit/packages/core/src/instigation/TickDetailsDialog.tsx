import {gql, useQuery} from '@apollo/client';
import 'chartjs-adapter-date-fns';
import {Button, DialogBody, DialogFooter, Dialog, Group, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {copyValue} from '../app/DomUtils';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {InstigationSelector, InstigationTickStatus} from '../types/globalTypes';

import {FailedRunList, RunList, TickTag, TICK_TAG_FRAGMENT} from './InstigationTick';
import {SelectedTickQuery, SelectedTickQueryVariables} from './types/SelectedTickQuery';

export const TickDetailsDialog: React.FC<{
  timestamp: number | undefined;
  instigationSelector: InstigationSelector;
  onClose: () => void;
}> = ({timestamp, instigationSelector, onClose}) => {
  const {data} = useQuery<SelectedTickQuery, SelectedTickQueryVariables>(JOB_SELECTED_TICK_QUERY, {
    variables: {instigationSelector, timestamp: timestamp || 0},
    fetchPolicy: 'cache-and-network',
    skip: !timestamp,
    partialRefetch: true,
  });

  const tick =
    data?.instigationStateOrError.__typename === 'InstigationState'
      ? data?.instigationStateOrError.tick
      : undefined;

  return (
    <Dialog
      isOpen={!!tick}
      onClose={onClose}
      style={{
        width: tick && tick.status === InstigationTickStatus.SKIPPED ? '50vw' : '90vw',
      }}
      title={tick ? <TimestampDisplay timestamp={tick.timestamp} /> : null}
    >
      {tick ? (
        <DialogBody>
          {tick.status === InstigationTickStatus.SUCCESS ? (
            tick.runIds.length ? (
              <RunList runIds={tick.runIds} />
            ) : (
              <FailedRunList originRunIds={tick.originRunIds} />
            )
          ) : null}
          {tick.status === InstigationTickStatus.SKIPPED ? (
            <Group direction="row" spacing={16}>
              <TickTag tick={tick} />
              <span>{tick.skipReason || 'No skip reason provided'}</span>
            </Group>
          ) : tick.status === InstigationTickStatus.FAILURE && tick.error ? (
            <PythonErrorInfo error={tick.error} />
          ) : undefined}
        </DialogBody>
      ) : null}
      <DialogFooter>
        <Button
          icon={<Icon name="copy_to_clipboard" />}
          onClick={(e) => copyValue(e, window.location.href)}
        >
          Copy Link
        </Button>
        <Button intent="primary" onClick={onClose}>
          OK
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const JOB_SELECTED_TICK_QUERY = gql`
  query SelectedTickQuery($instigationSelector: InstigationSelector!, $timestamp: Float!) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      __typename
      ... on InstigationState {
        id
        tick(timestamp: $timestamp) {
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
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
`;
