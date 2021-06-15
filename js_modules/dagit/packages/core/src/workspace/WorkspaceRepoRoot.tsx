import {Colors, Tab, Tabs} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Redirect, Route, Switch} from 'react-router-dom';

import {featureEnabled, FeatureFlag} from '../app/Util';
import {SchedulesRoot} from '../schedules/SchedulesRoot';
import {SensorsRoot} from '../sensors/SensorsRoot';
import {SolidsRoot} from '../solids/SolidsRoot';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';

import {RepositoryGraphsList} from './RepositoryGraphsList';
import {RepositoryPipelinesList} from './RepositoryPipelinesList';
import {repoAddressAsString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {workspacePathFromAddress} from './workspacePath';

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

  if (featureEnabled(FeatureFlag.PipelineModeTuples)) {
    tabs.splice(0, 1, {text: 'Jobs', href: workspacePathFromAddress(repoAddress, '/jobs')});
    tabs.splice(1, 0, {text: 'Graphs', href: workspacePathFromAddress(repoAddress, '/graphs')});
  }

  const activeTab = () => {
    switch (tab) {
      case 'schedules':
        return 'Schedules';
      case 'sensors':
        return 'Sensors';
      case 'solids':
        return 'Solids';
      case 'graphs':
        return 'Graphs';
      case 'jobs':
        return 'Jobs';
      case 'pipelines':
        return 'Pipelines';
      default:
        return featureEnabled(FeatureFlag.PipelineModeTuples) ? 'Pipelines' : 'Jobs';
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
          {featureEnabled(FeatureFlag.PipelineModeTuples) && (
            <Redirect from={'/workspace/:repoPath/pipelines'} to={'/workspace/:repoPath/jobs'} />
          )}
          <Route
            path={['/workspace/:repoPath/pipelines', '/workspace/:repoPath/jobs']}
            render={() => <RepositoryPipelinesList repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/graphs"
            exact
            render={() => <RepositoryGraphsList repoAddress={repoAddress} />}
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
