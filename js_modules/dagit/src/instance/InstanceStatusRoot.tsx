import {gql, useQuery} from '@apollo/client';
import {Tab, Tabs, Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Route, Switch} from 'react-router-dom';

import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {QueryCountdown} from 'src/app/QueryCountdown';
import {InstanceConfig} from 'src/instance/InstanceConfig';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {InstanceHealthPage} from 'src/instance/InstanceHealthPage';
import {InstanceSchedules} from 'src/instance/InstanceSchedules';
import {InstanceSensors} from 'src/instance/InstanceSensors';
import {InstanceHealthQuery} from 'src/instance/types/InstanceHealthQuery';
import {JOB_STATE_FRAGMENT} from 'src/jobs/JobUtils';
import {SCHEDULE_FRAGMENT} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';
import {SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';
import {Heading} from 'src/ui/Text';
import {REPOSITORY_INFO_FRAGMENT} from 'src/workspace/RepositoryInformation';
import {REPOSITORY_LOCATIONS_FRAGMENT} from 'src/workspace/WorkspaceContext';

const POLL_INTERVAL = 15 * 1000;

interface Props {
  tab: string;
}

export const InstanceStatusRoot = (props: Props) => {
  const {tab} = props;
  const queryData = useQuery<InstanceHealthQuery>(INSTANCE_HEALTH_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: POLL_INTERVAL,
    notifyOnNetworkStatusChange: true,
  });

  return (
    <Page>
      <Group direction="column" spacing={24}>
        <Group direction="column" spacing={12}>
          <PageHeader title={<Heading>Instance status</Heading>} />
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
              <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryData} />
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
  ${PYTHON_ERROR_FRAGMENT}
  ${SENSOR_FRAGMENT}
  ${JOB_STATE_FRAGMENT}
`;
