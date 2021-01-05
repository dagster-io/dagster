import {gql, NetworkStatus, useQuery} from '@apollo/client';
import {Tab, Tabs, Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Route, Switch} from 'react-router-dom';

import {JOB_STATE_FRAGMENT} from 'src/JobUtils';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {REPOSITORY_INFO_FRAGMENT} from 'src/RepositoryInformation';
import {InstanceConfig} from 'src/instance/InstanceConfig';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {InstanceHealthPage} from 'src/instance/InstanceHealthPage';
import {InstanceSchedules} from 'src/instance/InstanceSchedules';
import {InstanceSensors} from 'src/instance/InstanceSensors';
import {InstanceHealthQuery} from 'src/instance/types/InstanceHealthQuery';
import {SCHEDULE_FRAGMENT} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';
import {SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {Box} from 'src/ui/Box';
import {useCountdown} from 'src/ui/Countdown';
import {Group} from 'src/ui/Group';
import {Page} from 'src/ui/Page';
import {RefreshableCountdown} from 'src/ui/RefreshableCountdown';
import {Heading} from 'src/ui/Text';
import {REPOSITORY_LOCATIONS_FRAGMENT} from 'src/workspace/WorkspaceContext';

const POLL_INTERVAL = 15 * 1000;

interface Props {
  tab: string;
}

export const InstanceStatusRoot = (props: Props) => {
  const {tab} = props;
  const queryData = useQuery<InstanceHealthQuery>(INSTANCE_HEALTH_QUERY, {
    fetchPolicy: 'network-only',
    pollInterval: POLL_INTERVAL,
    notifyOnNetworkStatusChange: true,
  });

  const {networkStatus, refetch} = queryData;

  const countdownStatus = networkStatus === NetworkStatus.ready ? 'counting' : 'idle';
  const timeRemaining = useCountdown({
    duration: POLL_INTERVAL,
    status: countdownStatus,
  });
  const countdownRefreshing = countdownStatus === 'idle' || timeRemaining === 0;

  return (
    <Page>
      <Group direction="column" spacing={24}>
        <Group direction="column" spacing={12}>
          <Heading>Instance status</Heading>
          <Box
            flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}
            border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
          >
            <Tabs selectedTabId={tab}>
              <Tab id="health" title={<Link to="/instance/health">Health</Link>} />
              <Tab id="schedules" title={<Link to="/instance/schedules">Schedules</Link>} />
              <Tab id="sensors" title={<Link to="/instance/sensors">Sensors</Link>} />
              <Tab id="config" title={<Link to="/instance/config">Configuration</Link>} />
            </Tabs>
            <Box padding={{bottom: 8}}>
              <RefreshableCountdown
                refreshing={countdownRefreshing}
                seconds={Math.floor(timeRemaining / 1000)}
                onRefresh={() => refetch()}
              />
            </Box>
          </Box>
        </Group>
        <Switch>
          <Route
            path="/instance/health"
            render={() => <InstanceHealthPage queryData={queryData} />}
          />
          <Route
            path="/instance/schedules"
            render={() => <InstanceSchedules queryData={queryData} />}
          />
          <Route
            path="/instance/sensors"
            render={() => <InstanceSensors queryData={queryData} />}
          />
          <Route path="/instance/config" render={() => <InstanceConfig />} />
        </Switch>
      </Group>
    </Page>
  );
};

const INSTANCE_HEALTH_QUERY = gql`
  query InstanceHealthQuery {
    instance {
      ...InstanceHealthFragment
    }
    repositoryLocationsOrError {
      ...RepositoryLocationsFragment
    }
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          id
          name
          ...RepositoryInfoFragment
          schedules {
            id
            ...ScheduleFragment
          }
          sensors {
            id
            ...SensorFragment
          }
        }
      }
      ...PythonErrorFragment
    }
    scheduler {
      ...SchedulerFragment
    }
    unloadableJobStatesOrError {
      ... on JobStates {
        results {
          id
          ...JobStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
  ${REPOSITORY_LOCATIONS_FRAGMENT}
  ${REPOSITORY_INFO_FRAGMENT}
  ${SCHEDULE_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${SENSOR_FRAGMENT}
  ${JOB_STATE_FRAGMENT}
`;
