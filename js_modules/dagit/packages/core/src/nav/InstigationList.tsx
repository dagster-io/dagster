import {gql, useApolloClient} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {BorderSetting} from '../ui/types';
import {DagsterRepoOption} from '../workspace/WorkspaceContext';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

import {InstigationListQuery} from './types/InstigationListQuery';

type Item = {
  to: string;
  label: string;
  repoPath: string;
  instigationType: InstigationType;
  status: InstigationStatus;
};

interface InstigationListProps {
  selector?: string;
  repos: DagsterRepoOption[];
  repoPath?: string;
}

export const InstigationList: React.FC<InstigationListProps> = ({repos, repoPath, selector}) => {
  const client = useApolloClient();
  const [instigationList, setInstigationList] = React.useState<{
    schedules: {[key: string]: Item};
    sensors: {[key: string]: Item};
  }>(() => ({
    schedules: {},
    sensors: {},
  }));

  const activeRepos = new Set(
    repos.map((repo) => buildRepoPath(repo.repository.name, repo.repositoryLocation.name)),
  );

  React.useEffect(() => {
    const fetchInstigationList = () => {
      const subscriptions = repos.map((repo) => {
        return client
          .watchQuery<InstigationListQuery>({
            query: INSTIGATION_LIST_QUERY,
            variables: {
              repositorySelector: {
                repositoryLocationName: repo.repositoryLocation.name,
                repositoryName: repo.repository.name,
              },
            },
          })
          .subscribe({
            next: ({data}) => {
              const {schedulesOrError, sensorsOrError} = data;

              const scheduleUpdates = {};
              if (schedulesOrError.__typename === 'Schedules') {
                schedulesOrError.results.forEach(({name, scheduleState}) => {
                  const to = workspacePath(
                    scheduleState.repositoryOrigin.repositoryName,
                    scheduleState.repositoryOrigin.repositoryLocationName,
                    `/schedules/${name}`,
                  );

                  scheduleUpdates[to] = {
                    to,
                    label: name,
                    repoPath: buildRepoPath(
                      scheduleState.repositoryOrigin.repositoryName,
                      scheduleState.repositoryOrigin.repositoryLocationName,
                    ),
                    instigationType: InstigationType.SCHEDULE,
                    status: scheduleState.status,
                  };
                });
              }

              const sensorUpdates = {};
              if (sensorsOrError.__typename === 'Sensors') {
                sensorsOrError.results.forEach(({name, sensorState}) => {
                  const to = workspacePath(
                    sensorState.repositoryOrigin.repositoryName,
                    sensorState.repositoryOrigin.repositoryLocationName,
                    `/sensors/${name}`,
                  );

                  sensorUpdates[to] = {
                    to,
                    label: name,
                    repoPath: buildRepoPath(
                      sensorState.repositoryOrigin.repositoryName,
                      sensorState.repositoryOrigin.repositoryLocationName,
                    ),
                    instigationType: InstigationType.SENSOR,
                    status: sensorState.status,
                  };
                });
              }

              setInstigationList((current) => ({
                schedules: {...current.schedules, ...scheduleUpdates},
                sensors: {...current.sensors, ...sensorUpdates},
              }));
            },
          });
      });

      return subscriptions;
    };

    const subs = fetchInstigationList();

    return () => {
      subs.forEach((s) => s.unsubscribe());
    };
  }, [client, repos]);

  const schedules = Object.values(instigationList.schedules).filter(({repoPath}) =>
    activeRepos.has(repoPath),
  );
  const sensors = Object.values(instigationList.sensors).filter(({repoPath}) =>
    activeRepos.has(repoPath),
  );

  if (!schedules.length && !sensors.length) {
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

  const items = [...schedules, ...sensors];

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
        flex={{alignItems: 'center'}}
        border={{side: 'bottom', width: 1, color: Colors.DARK_GRAY3}}
      >
        <Item to="/instance/schedules">
          <Group direction="row" spacing={8} alignItems="center">
            <IconWIP name="schedule" color={ColorsWIP.Gray200} />
            <div>All schedules</div>
          </Group>
        </Item>
        <Box border={{width: 1, side: 'left', color: Colors.DARK_GRAY4}} margin={{horizontal: 8}}>
          &nbsp;
        </Box>
        <Item to="/instance/sensors">
          <Group direction="row" spacing={8} alignItems="center">
            <IconWIP name="sensors" color={ColorsWIP.Gray200} />
            <div>All sensors</div>
          </Group>
        </Item>
      </Box>
      <Items>
        {items.map((p) => {
          const isSelected = p.label === selector && p.repoPath === repoPath;
          const border: BorderSetting | null = isSelected
            ? {side: 'left', width: 4, color: isSelected ? Colors.COBALT3 : Colors.GRAY3}
            : null;
          const icon = p.instigationType === InstigationType.SCHEDULE ? 'schedule' : 'sensors';

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
                  <IconWIP name={icon} color={ColorsWIP.Gray200} />
                  <Label
                    data-tooltip={p.label}
                    data-tooltip-style={isSelected ? SelectedItemTooltipStyle : ItemTooltipStyle}
                  >
                    {p.label}
                  </Label>
                </Box>
                {p.status === InstigationStatus.RUNNING ? (
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
  max-height: calc((100vh - 390px) / 2);
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

const INSTIGATION_LIST_QUERY = gql`
  query InstigationListQuery($repositorySelector: RepositorySelector!) {
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
