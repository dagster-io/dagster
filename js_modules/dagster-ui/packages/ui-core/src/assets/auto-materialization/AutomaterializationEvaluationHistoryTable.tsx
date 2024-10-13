import {
  Body2,
  Box,
  Button,
  ButtonGroup,
  ButtonLink,
  CursorHistoryControls,
  CursorPaginationProps,
  Icon,
  MenuItem,
  Select,
  Spinner,
  Table,
} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {AssetDaemonTickFragment} from './types/AssetDaemonTicksQuery.types';
import {Timestamp} from '../../app/time/Timestamp';
import {InstigationTickStatus} from '../../graphql/types';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {TickStatusTag} from '../../ticks/TickStatusTag';

interface Props {
  loading: boolean;
  ticks: AssetDaemonTickFragment[];
  tickStatus: AutomaterializationTickStatusDisplay;
  setTickStatus: (status: AutomaterializationTickStatusDisplay) => void;
  setSelectedTick: (tick: AssetDaemonTickFragment | null) => void;
  setTableView: (view: 'evaluations' | 'runs') => void;
  paginationProps: CursorPaginationProps;
}

export const AutomaterializationEvaluationHistoryTable = ({
  loading,
  ticks,
  tickStatus,
  setTickStatus,
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
        <StatusFilter status={tickStatus} onChange={setTickStatus} />
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

export enum AutomaterializationTickStatusDisplay {
  ALL = 'all',
  FAILED = 'failed',
  SUCCESS = 'success',
}
export const AutomaterializationTickStatusDisplayMappings = {
  [AutomaterializationTickStatusDisplay.ALL]: [
    InstigationTickStatus.SUCCESS,
    InstigationTickStatus.FAILURE,
    InstigationTickStatus.STARTED,
    InstigationTickStatus.SKIPPED,
  ],
  [AutomaterializationTickStatusDisplay.FAILED]: [InstigationTickStatus.FAILURE],
  [AutomaterializationTickStatusDisplay.SUCCESS]: [InstigationTickStatus.SUCCESS],
};

const StatusFilterItems = [
  {key: AutomaterializationTickStatusDisplay.ALL, label: 'All ticks'},
  {key: AutomaterializationTickStatusDisplay.SUCCESS, label: 'Requested'},
  {key: AutomaterializationTickStatusDisplay.FAILED, label: 'Failed'},
];
const StatusFilter = ({
  status,
  onChange,
}: {
  status: AutomaterializationTickStatusDisplay;
  onChange: (value: AutomaterializationTickStatusDisplay) => void;
}) => {
  const activeItem = StatusFilterItems.find(({key}) => key === status);
  return (
    <Select<(typeof StatusFilterItems)[0]>
      popoverProps={{position: 'bottom-right'}}
      filterable={false}
      activeItem={activeItem}
      items={StatusFilterItems}
      itemRenderer={(item, props) => {
        return (
          <MenuItem
            active={props.modifiers.active}
            onClick={props.handleClick}
            key={item.key}
            text={item.label}
            style={{width: '300px'}}
          />
        );
      }}
      onItemSelect={(item) => onChange(item.key)}
    >
      <Button
        rightIcon={<Icon name="arrow_drop_down" />}
        style={{minWidth: '200px', display: 'flex', justifyContent: 'space-between'}}
      >
        {activeItem?.label}
      </Button>
    </Select>
  );
};

const TableWrapper = styled(Table)`
  th,
  td {
    vertical-align: middle !important;
  }
`;
