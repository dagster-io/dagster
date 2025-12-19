import {Body, Box, Colors, Icon, NonIdealState, Tooltip} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {RunsFeedTableWithFilters} from '../runs/RunsFeedTable';

export const RunList = ({runIds}: {runIds: string[]}) => {
  const filter = useMemo(
    () => ({
      runIds,
    }),
    [runIds],
  );

  return (
    <Box padding={{bottom: 8}}>
      <RunsFeedTableWithFilters filter={filter} includeRunsFromBackfills />
    </Box>
  );
};

export const TargetedRunList = ({originRunIds}: {originRunIds?: string[]}) => {
  if (!originRunIds || !originRunIds.length) {
    return null;
  }
  return (
    <Box flex={{direction: 'column', gap: 16}}>
      <Box padding={12} border={{side: 'bottom', color: Colors.textLighter()}}>
        <Body>
          Targeted Runs
          <Tooltip content="Runs this tick reacted on and reported back to.">
            <Icon name="info" color={Colors.textLight()} />
          </Tooltip>
        </Body>
        <RunList runIds={originRunIds} />
      </Box>
      <Box padding={12} margin={{bottom: 8}}>
        <Body>
          Requested Runs
          <Tooltip content="Runs launched by the run requests in this tick.">
            <Icon name="info" color={Colors.textLight()} />
          </Tooltip>
        </Body>
        <NonIdealState
          icon="sensors"
          title="No runs to display"
          description="This sensor does not target a pipeline or job."
        />
      </Box>
    </Box>
  );
};

export const TICK_TAG_FRAGMENT = gql`
  fragment TickTagFragment on InstigationTick {
    id
    status
    timestamp
    skipReason
    runIds
    runKeys
    error {
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
