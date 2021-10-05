import * as React from 'react';
import {Link, Redirect, Route, Switch} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {SchedulesRoot} from '../schedules/SchedulesRoot';
import {SensorsRoot} from '../sensors/SensorsRoot';
import {SolidsRoot} from '../solids/SolidsRoot';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {PageHeader} from '../ui/PageHeader';
import {Tab, Tabs} from '../ui/Tabs';
import {Heading} from '../ui/Text';

import {RepositoryAssetsList} from './RepositoryAssetsList';
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
  const {flagPipelineModeTuples, flagAssetGraph} = useFeatureFlags();

  const tabs = [
    {text: 'Pipelines', href: workspacePathFromAddress(repoAddress, '/pipelines')},
    {
      text: flagPipelineModeTuples ? 'Ops' : 'Solids',
      href: workspacePathFromAddress(repoAddress, flagPipelineModeTuples ? '/ops' : '/solids'),
    },
    {text: 'Schedules', href: workspacePathFromAddress(repoAddress, '/schedules')},
    {text: 'Sensors', href: workspacePathFromAddress(repoAddress, '/sensors')},
  ];

  if (flagPipelineModeTuples) {
    tabs.splice(0, 1, {text: 'Jobs', href: workspacePathFromAddress(repoAddress, '/jobs')});
    tabs.splice(1, 0, {text: 'Graphs', href: workspacePathFromAddress(repoAddress, '/graphs')});
  }

  if (flagAssetGraph) {
    tabs.push({
      text: 'Assets',
      href: workspacePathFromAddress(repoAddress, '/assets'),
    });
  }

  const activeTab = () => {
    switch (tab) {
      case 'schedules':
        return 'Schedules';
      case 'sensors':
        return 'Sensors';
      case 'solids':
        return 'Solids';
      case 'ops':
        return 'Ops';
      case 'graphs':
        return 'Graphs';
      case 'jobs':
        return 'Jobs';
      case 'pipelines':
        return 'Pipelines';
      case 'assets':
        return 'Assets';
      default:
        return flagPipelineModeTuples ? 'Pipelines' : 'Jobs';
    }
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%'}}>
      <Group direction="column" spacing={16} padding={{top: 16, horizontal: 24}}>
        <PageHeader
          title={<Heading>{path}</Heading>}
          icon="repo"
          description={<Link to="/workspace">Repository</Link>}
        />
        <Box border={{side: 'bottom', width: 1, color: ColorsWIP.Gray100}}>
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
            path="/workspace/:repoPath/assets(/?.*)"
            render={() => <RepositoryAssetsList repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/ops/:name?"
            render={(props) => (
              <SolidsRoot name={props.match.params.name} repoAddress={repoAddress} />
            )}
          />
          <Route
            path="/workspace/:repoPath/solids/:name?"
            render={(props) => {
              if (flagPipelineModeTuples) {
                return <Redirect to={props.match.url.replace(/\/solids\/?/, '/ops/')} />;
              }
              return <SolidsRoot name={props.match.params.name} repoAddress={repoAddress} />;
            }}
          />
          {flagPipelineModeTuples && (
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
