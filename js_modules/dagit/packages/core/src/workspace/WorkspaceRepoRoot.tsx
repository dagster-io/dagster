import {Box, PageHeader, Tabs, Tag, Heading} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect, Route, Switch, useParams} from 'react-router-dom';
import styled from 'styled-components/macro';

import {OpsRoot} from '../ops/OpsRoot';
import {SchedulesRoot} from '../schedules/SchedulesRoot';
import {SensorsRoot} from '../sensors/SensorsRoot';
import {TabLink} from '../ui/TabLink';

import {RepositoryAssetsList} from './RepositoryAssetsList';
import {RepositoryGraphsList} from './RepositoryGraphsList';
import {RepositoryPipelinesList} from './RepositoryPipelinesList';
import {useRepository} from './WorkspaceContext';
import {repoAddressAsString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {workspacePathFromAddress} from './workspacePath';

interface Props {
  repoAddress: RepoAddress;
}

export const WorkspaceRepoRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const {tab} = useParams<{tab?: string}>();

  const path = repoAddressAsString(repoAddress);
  const repo = useRepository(repoAddress);

  const anyPipelines = React.useMemo(() => {
    return repo?.repository.pipelines.some((pipelineOrJob) => !pipelineOrJob.isJob);
  }, [repo]);

  const tabs = React.useMemo(() => {
    const tabList = [
      {
        text: 'Assets',
        href: workspacePathFromAddress(repoAddress, '/assets'),
      },
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
    ];

    return tabList.filter(Boolean) as {text: string; href: string}[];
  }, [anyPipelines, repoAddress]);

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
        tags={<Tag icon="folder">Repository</Tag>}
        tabs={
          <Tabs size="small" selectedTabId={activeTab()}>
            {tabs.map(({href, text}) => (
              <TabLink key={text} id={text} title={text} to={href} />
            ))}
          </Tabs>
        }
      />
      <Container>
        <Switch>
          <Route path="/workspace/:repoPath/schedules">
            <SchedulesRoot repoAddress={repoAddress} />
          </Route>
          <Route path="/workspace/:repoPath/sensors">
            <SensorsRoot repoAddress={repoAddress} />
          </Route>
          <Route path="/workspace/:repoPath/assets(/?.*)">
            <RepositoryAssetsList repoAddress={repoAddress} />
          </Route>
          <Route path="/workspace/:repoPath/ops/:name?">
            <OpsRoot repoAddress={repoAddress} />
          </Route>
          <Route
            path="/workspace/:repoPath/solids/:name?"
            render={(props) => <Redirect to={props.match.url.replace(/\/solids\/?/, '/ops/')} />}
          />
          <Route path="/workspace/:repoPath/pipelines">
            <RepositoryPipelinesList display="pipelines" repoAddress={repoAddress} />
          </Route>
          <Route path="/workspace/:repoPath/jobs">
            <RepositoryPipelinesList display="jobs" repoAddress={repoAddress} />
          </Route>
          <Route path="/workspace/:repoPath/graphs" exact>
            <RepositoryGraphsList repoAddress={repoAddress} />
          </Route>
          <Route path="/workspace/:repoPath/(.*)?" render={() => <Redirect to={tabs[0].href} />} />
        </Switch>
      </Container>
    </Box>
  );
};

const Container = styled.div`
  flex: 1;
  flex-grow: 1;
  min-height: 0;
`;
