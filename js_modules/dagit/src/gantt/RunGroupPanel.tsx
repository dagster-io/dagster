import {gql, useQuery} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from 'src/app/CustomAlertProvider';
import {
  RunGroupPanelQuery,
  RunGroupPanelQuery_runGroupOrError_RunGroup_runs,
} from 'src/gantt/types/RunGroupPanelQuery';
import {RunStatus} from 'src/runs/RunStatusDots';
import {DagsterTag} from 'src/runs/RunTag';
import {RunElapsed, RunTime, RUN_TIME_FRAGMENT} from 'src/runs/RunUtils';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';

function subsetTitleForRun(run: {tags: {key: string; value: string}[]}) {
  const stepsTag = run.tags.find((t) => t.key === DagsterTag.StepSelection);
  return stepsTag ? stepsTag.value : '*';
}

export const RunGroupPanel: React.FunctionComponent<{runId: string}> = ({runId}) => {
  const queryResult = useQuery<RunGroupPanelQuery>(RUN_GROUP_PANEL_QUERY, {
    variables: {runId},
    fetchPolicy: 'cache-and-network',
    pollInterval: 3000,
  });

  const group = queryResult.data?.runGroupOrError;

  if (!group || group.__typename === 'RunGroupNotFoundError') {
    return <div />;
  }
  if (group.__typename === 'PythonError') {
    return (
      <Group direction="row" spacing={8} padding={8}>
        <Icon
          icon="warning-sign"
          color={Colors.GOLD3}
          iconSize={13}
          style={{position: 'relative', top: '-1px'}}
        />
        <div style={{fontSize: '13px'}}>
          The run group for this run could not be loaded.{' '}
          <ButtonLink
            color={Colors.BLUE3}
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
    return <div />;
  }

  const runs = (group.runs || []).filter((g) => g !== null);

  return (
    <RunGroupContainer>
      {runs[0] && <RunGroupHeader>{runs[0].pipelineName}</RunGroupHeader>}
      {runs.map((g: RunGroupPanelQuery_runGroupOrError_RunGroup_runs, idx) => (
        <RunGroupRun key={g.runId} to={`/instance/runs/${g.runId}`} selected={g.runId === runId}>
          {idx < runs.length - 1 && <ThinLine style={{height: 36}} />}
          <Box padding={{top: 4}}>
            <RunStatus status={g.status} />
          </Box>

          <div
            style={{
              flex: 1,
              marginLeft: 5,
              minWidth: 0,
              color: Colors.DARK_GRAY5,
            }}
          >
            <div style={{display: 'flex', justifyContent: 'space-between'}}>
              <RunTitle>
                {g.runId.split('-')[0]}
                {idx === 0 && RootTag}
              </RunTitle>
              <RunTime run={g} size="minimal" />
            </div>

            <div
              style={{
                display: 'flex',
                color: Colors.DARK_GRAY5,
                justifyContent: 'space-between',
              }}
            >
              {subsetTitleForRun(g)}
              <RunElapsed run={g} />
            </div>
          </div>
        </RunGroupRun>
      ))}
    </RunGroupContainer>
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

const RunGroupContainer = styled.div`
  border-bottom: 2px solid ${Colors.GRAY5};
  overflow: scroll;
`;

const RunGroupRun = styled(Link)<{selected: boolean}>`
  align-items: flex-start;
  background: ${({selected}) => (selected ? Colors.LIGHT_GRAY2 : Colors.WHITE)};
  padding: 3px 6px;
  font-size: 13px;
  line-height: 20px;
  display: flex;
  position: relative;
  padding-left: 6px;
  &:hover {
    text-decoration: none;
    background: ${({selected}) => (selected ? Colors.LIGHT_GRAY2 : Colors.LIGHT_GRAY5)};
  }
`;

const ThinLine = styled.div`
  position: absolute;
  top: 17px;
  width: 1px;
  border-right: 1px solid rgba(0, 0, 0, 0.2);
  left: 11px;
  z-index: 2;
`;

const RunTitle = styled.span`
  color: ${Colors.BLACK};
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  user-select: text;
  flex: 1;
`;

const RunGroupHeader = styled.div`
  font-size: 11px;
  line-height: 15px;
  padding: 3px 6px;
  text-transform: uppercase;
  background: ${Colors.WHITE};
  border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  color: ${Colors.GRAY3};
  height: 20px;
`;

const RootTag = (
  <span
    style={{
      borderRadius: 2,
      fontSize: 12,
      lineHeight: '14px',
      background: 'rgb(118, 144, 188, 0.5)',
      color: 'white',
      padding: '0 4px',
      fontWeight: 400,
      userSelect: 'none',
      marginLeft: 4,
    }}
  >
    ROOT
  </span>
);
