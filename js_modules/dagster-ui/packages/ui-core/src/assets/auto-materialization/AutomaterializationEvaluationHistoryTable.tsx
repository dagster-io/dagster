import {
  Body2,
  Box,
  ButtonGroup,
  ButtonLink,
  Checkbox,
  CursorHistoryControls,
  CursorPaginationProps,
  Spinner,
  Table,
} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {AssetDaemonTickFragment} from './types/AssetDaemonTicksQuery.types';
import {Timestamp} from '../../app/time/Timestamp';
import {InstigationTickStatus} from '../../graphql/types';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {TickStatusTag} from '../../ticks/TickStatusTag';

interface Props {
  loading: boolean;
  ticks: AssetDaemonTickFragment[];
  statuses: Set<InstigationTickStatus>;
  setStatuses: (statuses: Set<InstigationTickStatus>) => void;
  setSelectedTick: (tick: AssetDaemonTickFragment | null) => void;
  setTableView: (view: 'evaluations' | 'runs') => void;
  paginationProps: CursorPaginationProps;
}

export const AutomaterializationEvaluationHistoryTable = ({
  loading,
  ticks,
  statuses,
  setStatuses,
  setSelectedTick,
  setTableView,
  paginationProps,
}: Props) => {
  return (
    <Box>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        padding={{vertical: 12, horizontal: 24}}
        margin={{top: 32}}
        border="top"
      >
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <ButtonGroup
            activeItems={new Set(['evaluations'])}
            buttons={[
              {id: 'evaluations', label: 'Evaluations'},
              {id: 'runs', label: 'Runs'},
            ]}
            onClick={(id: 'evaluations' | 'runs') => {
              setTableView(id);
            }}
          />
          {loading && !ticks?.length ? <Spinner purpose="body-text" /> : null}
        </Box>
        <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
          <StatusCheckbox
            statuses={statuses}
            setStatuses={setStatuses}
            status={InstigationTickStatus.STARTED}
          />
          <StatusCheckbox
            statuses={statuses}
            setStatuses={setStatuses}
            status={InstigationTickStatus.SUCCESS}
          />
          <StatusCheckbox
            statuses={statuses}
            setStatuses={setStatuses}
            status={InstigationTickStatus.FAILURE}
          />
          <StatusCheckbox
            statuses={statuses}
            setStatuses={setStatuses}
            status={InstigationTickStatus.SKIPPED}
          />
        </Box>
      </Box>
      <TableWrapper>
        <thead>
          <tr>
            <th style={{width: 120}}>Timestamp</th>
            <th style={{width: 90}}>Status</th>
            <th style={{width: 90}}>Duration</th>
            <th style={{width: 180}}>Result</th>
          </tr>
        </thead>
        <tbody>
          {/* Use previous data to stop page from jumping while new data loads */}
          {ticks.map((tick, index) => {
            // This is a hack for ticks that get stuck in started
            const isTickStuckInStartedState =
              index !== 0 &&
              tick.status === InstigationTickStatus.STARTED &&
              !paginationProps.hasPrevCursor;

            return (
              <tr key={tick.id}>
                <td>
                  <Timestamp timestamp={{unix: tick.timestamp}} timeFormat={{showTimezone: true}} />
                </td>
                <td>
                  <TickStatusTag tick={tick} isStuckStarted={isTickStuckInStartedState} />
                </td>
                <td>
                  {isTickStuckInStartedState ? (
                    ' - '
                  ) : (
                    <TimeElapsed startUnix={tick.timestamp} endUnix={tick.endTimestamp} />
                  )}
                </td>
                <td>
                  {[InstigationTickStatus.SKIPPED, InstigationTickStatus.SUCCESS].includes(
                    tick.status,
                  ) ? (
                    <ButtonLink
                      onClick={() => {
                        setSelectedTick(tick);
                      }}
                    >
                      <Body2>
                        {tick.requestedAssetMaterializationCount} materializations requested
                      </Body2>
                    </ButtonLink>
                  ) : (
                    ' - '
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </TableWrapper>
      <div style={{paddingBottom: '16px'}}>
        <CursorHistoryControls {...paginationProps} />
      </div>
    </Box>
  );
};

const StatusLabels = {
  [InstigationTickStatus.SKIPPED]: 'None requested',
  [InstigationTickStatus.STARTED]: 'Started',
  [InstigationTickStatus.FAILURE]: 'Failed',
  [InstigationTickStatus.SUCCESS]: 'Requested',
};

function StatusCheckbox({
  status,
  statuses,
  setStatuses,
}: {
  status: InstigationTickStatus;
  statuses: Set<InstigationTickStatus>;
  setStatuses: (statuses: Set<InstigationTickStatus>) => void;
}) {
  return (
    <Checkbox
      label={StatusLabels[status]}
      checked={statuses.has(status)}
      onChange={() => {
        const newStatuses = new Set(statuses);
        if (statuses.has(status)) {
          newStatuses.delete(status);
        } else {
          newStatuses.add(status);
        }
        setStatuses(newStatuses);
      }}
    />
  );
}

const TableWrapper = styled(Table)`
  th,
  td {
    vertical-align: middle !important;
  }
`;
