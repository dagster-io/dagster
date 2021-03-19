import {gql, useQuery} from '@apollo/client';
import {Tab, Tabs, Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Route, Switch} from 'react-router-dom';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {QueryCountdown} from '../app/QueryCountdown';
import {JOB_STATE_FRAGMENT} from '../jobs/JobUtils';
import {SCHEDULE_FRAGMENT} from '../schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT} from '../schedules/SchedulerInfo';
import {SENSOR_FRAGMENT} from '../sensors/SensorFragment';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';
import {REPOSITORY_INFO_FRAGMENT} from '../workspace/RepositoryInformation';
import {REPOSITORY_LOCATIONS_FRAGMENT} from '../workspace/WorkspaceContext';

import {InstanceBackfills} from './InstanceBackfills';
import {InstanceConfig} from './InstanceConfig';
import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {InstanceHealthPage} from './InstanceHealthPage';
import {InstanceSchedules} from './InstanceSchedules';
import {InstanceSensors} from './InstanceSensors';
import {InstanceHealthQuery} from './types/InstanceHealthQuery';

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
              <Tab id="backfills" title={<Link to="/instance/backfills">Backfills</Link>} />
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
          <Route
            path="/instance/backfills"
            render={() => <InstanceBackfills queryData={queryData} />}
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
