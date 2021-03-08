import {gql, useApolloClient} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {JobsListQuery} from 'src/nav/types/JobsListQuery';
import {JobStatus, JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {BorderSetting} from 'src/ui/types';
import {DagsterRepoOption} from 'src/workspace/WorkspaceContext';
import {workspacePath} from 'src/workspace/workspacePath';

type Item = {
  to: string;
  label: string;
  jobType: JobType;
  status: JobStatus;
};

interface JobsListProps {
  selector?: string;
  repos: DagsterRepoOption[];
}

export const JobsList: React.FunctionComponent<JobsListProps> = ({repos, selector}) => {
  const client = useApolloClient();
  const [jobs, setJobs] = React.useState<{schedules: Item[]; sensors: Item[]}>(() => ({
    schedules: [],
    sensors: [],
  }));

  React.useEffect(() => {
    const fetchJobs = async () => {
      const promises = repos.map((repo) =>
        client.query<JobsListQuery>({
          query: JOBS_LIST_QUERY,
          variables: {
            repositorySelector: {
              repositoryLocationName: repo.repositoryLocation.name,
              repositoryName: repo.repository.name,
            },
          },
        }),
      );

      const results = await Promise.all(promises);
      const schedules: Item[] = [];
      const sensors: Item[] = [];

      results.forEach((result) => {
        const {schedulesOrError, sensorsOrError} = result?.data;
        if (schedulesOrError.__typename === 'Schedules') {
          schedulesOrError.results.forEach(({name, scheduleState}) =>
            schedules.push({
              to: workspacePath(
                scheduleState.repositoryOrigin.repositoryName,
                scheduleState.repositoryOrigin.repositoryLocationName,
                `/schedules/${name}`,
              ),
              label: name,
              jobType: JobType.SCHEDULE,
              status: scheduleState.status,
            }),
          );
        }
        if (sensorsOrError.__typename === 'Sensors') {
          sensorsOrError.results.forEach(({name, sensorState}) =>
            sensors.push({
              to: workspacePath(
                sensorState.repositoryOrigin.repositoryName,
                sensorState.repositoryOrigin.repositoryLocationName,
                `/sensors/${name}`,
              ),
              label: name,
              jobType: JobType.SENSOR,
              status: sensorState.status,
            }),
          );
        }
      });

      setJobs({schedules, sensors});
    };

    fetchJobs();
  }, [client, repos]);

  if (!jobs.schedules.length && !jobs.sensors.length) {
    return (
      <div style={{flex: 1}}>
        <Box
          padding={12}
          style={{fontSize: '13px', color: Colors.LIGHT_GRAY3}}
          border={{width: 1, side: 'top', color: Colors.DARK_GRAY4}}
        >
          No schedules or sensors defined
        </Box>
      </div>
    );
  }

  const items = [...jobs.schedules, ...jobs.sensors];

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        borderTop: `1px solid ${Colors.DARK_GRAY4}`,
      }}
    >
      <Box
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        padding={{vertical: 8, horizontal: 12}}
        border={{side: 'bottom', width: 1, color: Colors.DARK_GRAY3}}
      >
        <ItemHeader>{'Schedules & Sensors'}</ItemHeader>
      </Box>
      <Box
        padding={{vertical: 8, horizontal: 12}}
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        border={{side: 'bottom', width: 1, color: Colors.DARK_GRAY3}}
      >
        <Item to="/instance/schedules">
          <Group direction="row" spacing={8} alignItems="center">
            <Icon icon="time" iconSize={14} />
            <div>All schedules</div>
          </Group>
        </Item>
        <Box border={{width: 1, side: 'left', color: Colors.DARK_GRAY4}}>&nbsp;</Box>
        <Item to="/instance/sensors">
          <Group direction="row" spacing={8} alignItems="center">
            <Icon icon="automatic-updates" iconSize={14} />
            <div>All sensors</div>
          </Group>
        </Item>
      </Box>
      <Items>
        {items.map((p) => {
          const isSelected = p.label === selector;
          const border: BorderSetting | null = isSelected
            ? {side: 'left', width: 4, color: isSelected ? Colors.COBALT3 : Colors.GRAY3}
            : null;
          const icon = p.jobType === JobType.SCHEDULE ? 'time' : 'automatic-updates';

          return (
            <Item key={p.to} className={`${isSelected ? 'selected' : ''}`} to={p.to}>
              <Box
                background={isSelected ? Colors.BLACK : null}
                border={border}
                flex={{alignItems: 'center', justifyContent: 'space-between'}}
                padding={{vertical: 8, right: 12, left: 12}}
              >
                <Box
                  flex={{alignItems: 'center', justifyContent: 'flex-start'}}
                  style={{overflow: 'hidden'}}
                >
                  <Icon icon={icon} iconSize={14} />
                  <Label
                    data-tooltip={p.label}
                    data-tooltip-style={isSelected ? SelectedItemTooltipStyle : ItemTooltipStyle}
                  >
                    {p.label}
                  </Label>
                </Box>
                {p.status === JobStatus.RUNNING ? (
                  <Box margin={{left: 4}}>
                    <StatusDot size={9} />
                  </Box>
                ) : null}
              </Box>
            </Item>
          );
        })}
      </Items>
    </div>
  );
};

const ItemHeader = styled.div`
  font-size: 15px;
  text-overflow: ellipsis;
  overflow: hidden;
  font-weight: bold;
  color: ${Colors.LIGHT_GRAY3} !important;
`;

const Label = styled.div`
  overflow: hidden;
  text-overflow: ellipsis;
  margin-left: 8px;
  white-space: nowrap;
`;

const StatusDot = styled.div<{
  size: number;
}>`
  width: ${({size}) => size}px;
  height: ${({size}) => size}px;
  border-radius: ${({size}) => size / 2}px;
  background: ${Colors.GREEN2};
`;

const Items = styled.div`
  flex: 1;
  overflow-y: auto;
  max-height: calc((100vh - 405px) / 2);
  &::-webkit-scrollbar {
    width: 11px;
  }

  scrollbar-width: thin;
  scrollbar-color: ${Colors.GRAY1} ${Colors.DARK_GRAY1};

  &::-webkit-scrollbar-track {
    background: ${Colors.DARK_GRAY1};
  }
  &::-webkit-scrollbar-thumb {
    background-color: ${Colors.GRAY1};
    border-radius: 6px;
    border: 3px solid ${Colors.DARK_GRAY1};
  }
`;

const Item = styled(Link)`
  font-size: 13px;
  color: ${Colors.LIGHT_GRAY3} !important;
  &:hover {
    text-decoration: none;
    color: ${Colors.WHITE} !important;
  }
  &:focus {
    outline: 0;
  }
  &.selected {
    font-weight: 600;
    color: ${Colors.WHITE} !important;
  }
`;

const BaseTooltipStyle = {
  fontSize: 13,
  padding: 3,
  paddingRight: 7,
  left: 9,
  top: 5,
  color: Colors.WHITE,
  background: Colors.DARK_GRAY1,
  transform: 'none',
  border: 0,
  borderRadius: 4,
};

const ItemTooltipStyle = JSON.stringify({
  ...BaseTooltipStyle,
  color: Colors.WHITE,
  background: Colors.DARK_GRAY1,
});

const SelectedItemTooltipStyle = JSON.stringify({
  ...BaseTooltipStyle,
  color: Colors.WHITE,
  background: Colors.BLACK,
  fontWeight: 600,
});

const JOBS_LIST_QUERY = gql`
  query JobsListQuery($repositorySelector: RepositorySelector!) {
    schedulesOrError(repositorySelector: $repositorySelector) {
      ... on Schedules {
        results {
          id
          name
          scheduleState {
            id
            repositoryOrigin {
              id
              repositoryName
              repositoryLocationName
            }
            status
          }
        }
      }
    }
    sensorsOrError(repositorySelector: $repositorySelector) {
      ... on Sensors {
        results {
          id
          name
          sensorState {
            id
            repositoryOrigin {
              id
              repositoryName
              repositoryLocationName
            }
            status
          }
        }
      }
    }
  }
`;
