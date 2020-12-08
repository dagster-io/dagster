import {gql, NetworkStatus, useQuery} from '@apollo/client';
import {Tab, Tabs, Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Route, Switch} from 'react-router-dom';

import {DAEMON_HEALTH_FRAGMENT} from 'src/instance/DaemonList';
import {InstanceDetails} from 'src/instance/InstanceDetails';
import {InstanceHealthPage} from 'src/instance/InstanceHealthPage';
import {InstanceHealthQuery} from 'src/instance/types/InstanceHealthQuery';
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
      <Group direction="vertical" spacing={24}>
        <Group direction="vertical" spacing={12}>
          <Heading>Instance details</Heading>
          <Box
            flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}
            border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
          >
            <Tabs selectedTabId={tab}>
              <Tab
                id="health"
                title={
                  <Link to="/instance/health">
                    <Group direction="horizontal" spacing={8}>
                      <div>Health</div>
                    </Group>
                  </Link>
                }
              />
              <Tab
                id="config"
                title={
                  <Link to="/instance/config">
                    <Group direction="horizontal" spacing={8}>
                      <div>Configuration</div>
                    </Group>
                  </Link>
                }
              />
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
          <Route path="/instance/config" render={() => <InstanceDetails />} />
        </Switch>
      </Group>
    </Page>
  );
};

const INSTANCE_HEALTH_FRAGMENT = gql`
  fragment InstanceHealthFragment on Instance {
    daemonHealth {
      ...DaemonHealthFragment
    }
  }
  ${DAEMON_HEALTH_FRAGMENT}
`;

const INSTANCE_HEALTH_QUERY = gql`
  query InstanceHealthQuery {
    repositoryLocationsOrError {
      ...RepositoryLocationsFragment
    }
    instance {
      ...InstanceHealthFragment
    }
  }
  ${REPOSITORY_LOCATIONS_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
`;
