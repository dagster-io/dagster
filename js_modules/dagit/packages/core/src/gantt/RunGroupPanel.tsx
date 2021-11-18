import {gql, useQuery} from '@apollo/client';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SidebarSection} from '../pipelines/SidebarComponents';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {DagsterTag} from '../runs/RunTag';
import {RunElapsed, RunTime, RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {FontFamily} from '../ui/styles';

import {RunGroupPanelQuery} from './types/RunGroupPanelQuery';

function subsetTitleForRun(run: {tags: {key: string; value: string}[]}) {
  const stepsTag = run.tags.find((t) => t.key === DagsterTag.StepSelection);
  return stepsTag ? stepsTag.value : '*';
}

export const RunGroupPanel: React.FC<{runId: string; runStatusLastChangedAt: number}> = ({
  runId,
  runStatusLastChangedAt,
}) => {
  const {data, refetch} = useQuery<RunGroupPanelQuery>(RUN_GROUP_PANEL_QUERY, {
    variables: {runId},
    fetchPolicy: 'cache-and-network',
    pollInterval: 15000, // 15s
  });

  // Because the RunGroupPanel makes it's own query for the runs and their statuses,
  // the log + gantt chart UI can show that the run is "completed" for up to 15s before
  // it's reflected in the sidebar. Observing this single timestamp from our parent
  // allows us to refetch data immediately when the run's exitedAt / startedAt, etc. is set.
  React.useEffect(() => {
    refetch();
  }, [refetch, runStatusLastChangedAt]);

  const group = data?.runGroupOrError;

  if (!group || group.__typename === 'RunGroupNotFoundError') {
    return null;
  }

  if (group.__typename === 'PythonError') {
    return (
      <Group direction="row" spacing={8} padding={8}>
        <IconWIP name="warning" color={ColorsWIP.Yellow500} />
        <div style={{fontSize: '13px'}}>
          The run group for this run could not be loaded.{' '}
          <ButtonLink
            color={ColorsWIP.Blue500}
            underline="always"
            onClick={() => {
              showCustomAlert({
                title: 'Python error',
                body: group.message,
              });
            }}
          >
            View error
          </ButtonLink>
        </div>
      </Group>
    );
  }

  if (group.runs?.length === 1) {
    return null;
  }

  // BG Note: the g.stats check is a fix for our storybook tests, something is wrong with the
  // apollo mocks for stats and I cannot figure it out.
  const runs = (group.runs || [])
    .filter(
      (g) =>
        g !== null &&
        g.stats.__typename === 'RunStatsSnapshot' &&
        typeof g.stats.startTime === 'number',
    )
    .sort((a, b) => {
      // We've already filtered out runs that don't have stats, but we need to appease TS here.
      const statsA = a?.stats;
      const statsB = b?.stats;
      if (statsA?.__typename === 'RunStatsSnapshot' && statsB?.__typename === 'RunStatsSnapshot') {
        return (statsB.startTime || 0) - (statsA.startTime || 0);
      }

      return 0;
    });

  return (
    <SidebarSection title={runs[0] ? `${runs[0].pipelineName} (${runs.length})` : ''}>
      <>
        {runs.map((g, idx) =>
          g ? (
            <RunGroupRun
              key={g.runId}
              to={`/instance/runs/${g.runId}`}
              selected={g.runId === runId}
            >
              {idx < runs.length - 1 && <ThinLine style={{height: 36}} />}
              <Box padding={{top: 4}}>
                <RunStatusIndicator status={g.status} />
              </Box>
              <div
                style={{
                  flex: 1,
                  marginLeft: 5,
                  minWidth: 0,
                  color: ColorsWIP.Gray700,
                }}
              >
                <div style={{display: 'flex', justifyContent: 'space-between'}}>
                  <RunTitle>
                    {g.runId.split('-')[0]}
                    {idx === runs.length - 1 && RootTag}
                  </RunTitle>
                  <RunTime run={g} />
                </div>
                <div
                  style={{
                    display: 'flex',
                    color: ColorsWIP.Gray700,
                    justifyContent: 'space-between',
                  }}
                >
                  {subsetTitleForRun(g)}
                  <RunElapsed run={g} />
                </div>
              </div>
            </RunGroupRun>
          ) : null,
        )}
      </>
    </SidebarSection>
  );
};

const RUN_GROUP_PANEL_QUERY = gql`
  query RunGroupPanelQuery($runId: ID!) {
    runGroupOrError(runId: $runId) {
      __typename
      ... on PythonError {
        message
      }
      ... on RunGroup {
        rootRunId
        runs {
          id
          runId
          parentRunId
          status
          stepKeysToExecute
          pipelineName
          tags {
            key
            value
          }
          ...RunTimeFragment
        }
      }
    }
  }
  ${RUN_TIME_FRAGMENT}
`;

const RunGroupRun = styled(Link)<{selected: boolean}>`
  align-items: flex-start;
  background: ${({selected}) => (selected ? ColorsWIP.Gray100 : ColorsWIP.White)};
  padding: 4px 6px 4px 24px;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  line-height: 20px;
  display: flex;
  position: relative;
  &:hover {
    text-decoration: none;
    background: ${({selected}) => (selected ? ColorsWIP.Gray100 : ColorsWIP.Gray50)};
  }
`;

const ThinLine = styled.div`
  position: absolute;
  top: 20px;
  width: 1px;
  background: ${ColorsWIP.Gray200};
  left: 29px;
  z-index: 2;
`;

const RunTitle = styled.span`
  color: ${ColorsWIP.Dark};
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  user-select: text;
  flex: 1;
`;

const RootTag = (
  <span
    style={{
      borderRadius: 2,
      fontSize: 12,
      lineHeight: '14px',
      background: ColorsWIP.Gray300,
      color: ColorsWIP.White,
      padding: '0 4px',
      fontWeight: 400,
      userSelect: 'none',
      marginLeft: 12,
    }}
  >
    ROOT
  </span>
);
