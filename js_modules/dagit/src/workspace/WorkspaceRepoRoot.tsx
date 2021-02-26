import {Colors, Tab, Tabs} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Redirect, Route, Switch} from 'react-router-dom';

import {SchedulesRoot} from 'src/schedules/SchedulesRoot';
import {SensorsRoot} from 'src/sensors/SensorsRoot';
import {SolidsRoot} from 'src/solids/SolidsRoot';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {PageHeader} from 'src/ui/PageHeader';
import {Heading} from 'src/ui/Text';
import {RepositoryPipelinesList} from 'src/workspace/RepositoryPipelinesList';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface Props {
  tab?: string;
  repoAddress: RepoAddress;
}

export const WorkspaceRepoRoot: React.FC<Props> = (props) => {
  const {repoAddress, tab} = props;
  const path = repoAddressAsString(repoAddress);

  const tabs = [
    {text: 'Pipelines', href: workspacePathFromAddress(repoAddress, '/pipelines')},
    {text: 'Solids', href: workspacePathFromAddress(repoAddress, '/solids')},
    {text: 'Schedules', href: workspacePathFromAddress(repoAddress, '/schedules')},
    {text: 'Sensors', href: workspacePathFromAddress(repoAddress, '/sensors')},
  ];

  const activeTab = () => {
    switch (tab) {
      case 'schedules':
        return 'Schedules';
      case 'sensors':
        return 'Sensors';
      case 'solids':
        return 'Solids';
      default:
        return 'Pipelines';
    }
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%'}}>
      <Group direction="column" spacing={16} padding={{top: 20, horizontal: 20}}>
        <PageHeader
          title={<Heading>{path}</Heading>}
          icon="cube"
          description={<Link to="/workspace">Repository</Link>}
        />
        <Box border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}>
          <Tabs large={false} selectedTabId={activeTab()}>
            {tabs.map((tab) => {
              const {href, text} = tab;
              return <Tab key={text} id={text} title={<Link to={href}>{text}</Link>} />;
            })}
          </Tabs>
        </Box>
      </Group>
      <div style={{flex: 1, flexGrow: 1}}>
        <Switch>
          <Route
            path="/workspace/:repoPath/schedules"
            render={() => <SchedulesRoot repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/sensors"
            render={() => <SensorsRoot repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/solids/:name?"
            render={(props) => (
              <SolidsRoot name={props.match.params.name} repoAddress={repoAddress} />
            )}
          />
          <Route
            path="/workspace/:repoPath/pipelines"
            render={() => <RepositoryPipelinesList repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/(.*)?"
            render={() => <Redirect to={workspacePathFromAddress(repoAddress, `/pipelines`)} />}
          />
        </Switch>
      </div>
    </Box>
  );
};
