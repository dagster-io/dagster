import {Box, ButtonLink, Colors, FontFamily, Group, Icon} from '@dagster-io/ui-components';
import {useEffect} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {gql, useQuery} from '../apollo-client';
import {
  RunGroupPanelQuery,
  RunGroupPanelQueryVariables,
  RunGroupPanelRunFragment,
} from './types/RunGroupPanel.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {SidebarSection} from '../pipelines/SidebarComponents';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {DagsterTag} from '../runs/RunTag';
import {RUN_TIME_FRAGMENT, RunStateSummary, RunTime} from '../runs/RunUtils';

type Run = RunGroupPanelRunFragment;

function subsetTitleForRun(run: {tags: {key: string; value: string}[]}) {
  const stepsTag = run.tags.find((t) => t.key === DagsterTag.StepSelection);
  return stepsTag ? stepsTag.value : '*';
}

export const RunGroupPanel = ({
  runId,
  runStatusLastChangedAt,
}: {
  runId: string;
  runStatusLastChangedAt: number;
}) => {
  const queryResult = useQuery<RunGroupPanelQuery, RunGroupPanelQueryVariables>(
    RUN_GROUP_PANEL_QUERY,
    {
      variables: {runId},
      notifyOnNetworkStatusChange: true,
    },
  );

  const {data, refetch} = queryResult;
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  // Because the RunGroupPanel makes it's own query for the runs and their statuses,
  // the log + gantt chart UI can show that the run is "completed" for up to 15s before
  // it's reflected in the sidebar. Observing this single timestamp from our parent
  // allows us to refetch data immediately when the run's exitedAt / startedAt, etc. is set.
  useEffect(() => {
    if (runStatusLastChangedAt) {
      refetch();
    }
  }, [refetch, runStatusLastChangedAt]);

  const group = data?.runGroupOrError;

  if (!group || group.__typename === 'RunGroupNotFoundError') {
    return null;
  }

  if (group.__typename === 'PythonError') {
    return (
      <Group direction="row" spacing={8} padding={8}>
        <Icon name="warning" color={Colors.accentYellow()} />
        <div style={{fontSize: '13px'}}>
          The run group for this run could not be loaded.{' '}
          <ButtonLink
            color={Colors.linkDefault()}
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

  const unsorted: Run[] = [];
  (group.runs || []).forEach((run: Run | null) => {
    if (run && typeof run.startTime === 'number') {
      unsorted.push(run);
    }
  });
  const runs: Run[] = unsorted.sort((a: Run, b: Run) => {
    return (a.startTime || 0) - (b.startTime || 0);
  });

  return (
    <SidebarSection title={runs[0] ? `Re-executions (${runs.length - 1})` : ''}>
      <>
        {runs.map((g, idx) =>
          g ? (
            <RunGroupRun key={g.id} to={`/runs/${g.id}`} selected={g.id === runId}>
              {idx < runs.length - 1 && <ThinLine style={{height: 36}} />}
              <Box padding={{top: 4}}>
                <RunStatusIndicator status={g.status} />
              </Box>
              <div
                style={{
                  flex: 1,
                  marginLeft: 5,
                  minWidth: 0,
                  color: Colors.textLight(),
                }}
              >
                <div style={{display: 'flex', justifyContent: 'space-between'}}>
                  <RunTitle>
                    {g.id.split('-')[0]}
                    {idx === 0 && RootTag}
                  </RunTitle>
                  <RunTime run={g} />
                </div>
                <div
                  style={{
                    display: 'flex',
                    color: Colors.textLight(),
                    justifyContent: 'space-between',
                  }}
                >
                  {subsetTitleForRun(g)}
                  <RunStateSummary run={g} />
                </div>
              </div>
            </RunGroupRun>
          ) : null,
        )}
      </>
    </SidebarSection>
  );
};

export const RUN_GROUP_PANEL_QUERY = gql`
  query RunGroupPanelQuery($runId: ID!) {
    runGroupOrError(runId: $runId) {
      ... on RunGroup {
        rootRunId
        runs {
          id
          ...RunGroupPanelRun
        }
      }
      ...PythonErrorFragment
    }
  }

  fragment RunGroupPanelRun on Run {
    id
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

  ${PYTHON_ERROR_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
`;

const RunGroupRun = styled(Link)<{selected: boolean}>`
  align-items: flex-start;
  background: ${({selected}) => (selected ? Colors.backgroundLight() : Colors.backgroundDefault())};
  padding: 4px 6px 4px 24px;
  font-family: ${FontFamily.monospace};
  font-size: 12px;
  line-height: 20px;
  display: flex;
  position: relative;
  &:hover {
    text-decoration: none;
    background: ${({selected}) =>
      selected ? Colors.backgroundLightHover() : Colors.backgroundDefaultHover()};
  }
`;

const ThinLine = styled.div`
  position: absolute;
  top: 20px;
  width: 1px;
  background: ${Colors.borderDefault()};
  left: 29px;
  z-index: 2;
`;

const RunTitle = styled.span`
  color: ${Colors.textDefault()};
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
      background: Colors.accentReversed(),
      color: Colors.accentPrimary(),
      padding: '0 4px',
      fontWeight: 400,
      userSelect: 'none',
      marginLeft: 12,
    }}
  >
    ROOT
  </span>
);
