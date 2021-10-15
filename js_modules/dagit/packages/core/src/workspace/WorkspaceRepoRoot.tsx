import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {SchedulesRoot} from '../schedules/SchedulesRoot';
import {SensorsRoot} from '../sensors/SensorsRoot';
import {SolidsRoot} from '../solids/SolidsRoot';
import {Box} from '../ui/Box';
import {PageHeader} from '../ui/PageHeader';
import {Tab, Tabs} from '../ui/Tabs';
import {TagWIP} from '../ui/TagWIP';
import {Heading} from '../ui/Text';

import {RepositoryAssetsList} from './RepositoryAssetsList';
import {RepositoryGraphsList} from './RepositoryGraphsList';
import {RepositoryPipelinesList} from './RepositoryPipelinesList';
import {useRepository} from './WorkspaceContext';
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
  const {flagAssetGraph} = useFeatureFlags();
  const repo = useRepository(repoAddress);

  const anyPipelines = React.useMemo(() => {
    return repo?.repository.pipelines.some((pipelineOrJob) => !pipelineOrJob.isJob);
  }, [repo]);

  const tabs = React.useMemo(() => {
    const tabList = [
      {text: 'Jobs', href: workspacePathFromAddress(repoAddress, '/jobs')},
      anyPipelines
        ? {text: 'Pipelines', href: workspacePathFromAddress(repoAddress, '/pipelines')}
        : null,
      {text: 'Graphs', href: workspacePathFromAddress(repoAddress, '/graphs')},
      {
        text: 'Ops',
        href: workspacePathFromAddress(repoAddress, '/ops'),
      },
      {text: 'Schedules', href: workspacePathFromAddress(repoAddress, '/schedules')},
      {text: 'Sensors', href: workspacePathFromAddress(repoAddress, '/sensors')},
      flagAssetGraph
        ? {
            text: 'Assets',
            href: workspacePathFromAddress(repoAddress, '/assets'),
          }
        : null,
    ];

    return tabList.filter(Boolean) as {text: string; href: string}[];
  }, [anyPipelines, flagAssetGraph, repoAddress]);

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
        return 'Jobs';
    }
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%'}}>
      <PageHeader
        title={<Heading>{path}</Heading>}
        tags={<TagWIP icon="folder">Repository</TagWIP>}
        tabs={
          <Tabs large={false} selectedTabId={activeTab()}>
            {tabs.map(({href, text}) => (
              <Tab key={text} id={text} title={text} to={href} />
            ))}
          </Tabs>
        }
      />
      <Container>
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
            render={(props) => <Redirect to={props.match.url.replace(/\/solids\/?/, '/ops/')} />}
          />
          <Route
            path="/workspace/:repoPath/pipelines"
            render={() => <RepositoryPipelinesList display="pipelines" repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/jobs"
            render={() => <RepositoryPipelinesList display="jobs" repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/graphs"
            exact
            render={() => <RepositoryGraphsList repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/(.*)?"
            render={() => <Redirect to={workspacePathFromAddress(repoAddress, `/jobs`)} />}
          />
        </Switch>
      </Container>
    </Box>
  );
};

const Container = styled.div`
  flex: 1;
  flex-grow: 1;
`;
