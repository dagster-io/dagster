import {Box} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Switch} from 'react-router-dom';

import {CodeLocationAssetsList} from './CodeLocationAssetsList';
import {CodeLocationGraphsList} from './CodeLocationGraphsList';
import {CodeLocationOpsView} from './CodeLocationOpsView';
import {CodeLocationSearchableList, SearchableListRow} from './CodeLocationSearchableList';
import {Route} from '../app/Route';
import {COMMON_COLLATOR} from '../app/Util';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {RepoAddress} from '../workspace/types';
import {WorkspaceRepositoryFragment} from '../workspace/types/WorkspaceQueries.types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  repoAddress: RepoAddress;
  repository: WorkspaceRepositoryFragment;
}

export const CodeLocationDefinitionsMain = ({repoAddress, repository}: Props) => {
  return (
    <Box flex={{direction: 'column', alignItems: 'stretch'}} style={{flex: 1, overflow: 'hidden'}}>
      <Switch>
        <Route path="/locations/:repoPath/assets">
          <CodeLocationAssetsList repoAddress={repoAddress} />
        </Route>
        <Route path="/locations/:repoPath/jobs">
          <CodeLocationJobsList repoAddress={repoAddress} repository={repository} />
        </Route>
        <Route path="/locations/:repoPath/sensors">
          <CodeLocationSensorsList repoAddress={repoAddress} repository={repository} />
        </Route>
        <Route path="/locations/:repoPath/schedules">
          <CodeLocationSchedulesList repoAddress={repoAddress} repository={repository} />
        </Route>
        <Route path="/locations/:repoPath/resources">
          <CodeLocationResourcesList repoAddress={repoAddress} repository={repository} />
        </Route>
        <Route path="/locations/:repoPath/graphs">
          <CodeLocationGraphsList repoAddress={repoAddress} />
        </Route>
        <Route path="/locations/:repoPath/ops/:name?">
          <CodeLocationOpsView repoAddress={repoAddress} />
        </Route>
      </Switch>
    </Box>
  );
};

const CodeLocationJobsList = (props: Props) => {
  const {repoAddress, repository} = props;
  const jobs = useMemo(
    () =>
      repository.pipelines
        .filter(({name}) => !isHiddenAssetGroupJob(name))
        .sort((a, b) => COMMON_COLLATOR.compare(a.name, b.name)),
    [repository],
  );

  return (
    <CodeLocationSearchableList
      items={jobs}
      placeholder="Search jobs by name…"
      nameFilter={(job, value) => job.name.toLowerCase().includes(value)}
      renderRow={(job) => (
        <SearchableListRow
          iconName="job"
          label={job.name}
          path={workspacePathFromAddress(repoAddress, `/jobs/${job.name}`)}
        />
      )}
    />
  );
};

const CodeLocationSensorsList = (props: Props) => {
  const {repoAddress, repository} = props;
  const sensors = useMemo(
    () => [...repository.sensors].sort((a, b) => COMMON_COLLATOR.compare(a.name, b.name)),
    [repository],
  );

  return (
    <CodeLocationSearchableList
      items={sensors}
      placeholder="Search sensors by name…"
      nameFilter={(sensor, value) => sensor.name.toLowerCase().includes(value)}
      renderRow={(sensor) => (
        <SearchableListRow
          iconName="sensors"
          label={sensor.name}
          path={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}
        />
      )}
    />
  );
};

const CodeLocationSchedulesList = (props: Props) => {
  const {repoAddress, repository} = props;
  const schedules = useMemo(
    () => [...repository.schedules].sort((a, b) => COMMON_COLLATOR.compare(a.name, b.name)),
    [repository],
  );

  return (
    <CodeLocationSearchableList
      items={schedules}
      placeholder="Search schedules by name…"
      nameFilter={(schedule, value) => schedule.name.toLowerCase().includes(value)}
      renderRow={(schedule) => (
        <SearchableListRow
          iconName="schedule"
          label={schedule.name}
          path={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}
        />
      )}
    />
  );
};

const CodeLocationResourcesList = (props: Props) => {
  const {repoAddress, repository} = props;
  const resources = useMemo(
    () =>
      [...repository.allTopLevelResourceDetails].sort((a, b) =>
        COMMON_COLLATOR.compare(a.name, b.name),
      ),
    [repository],
  );

  return (
    <CodeLocationSearchableList
      items={resources}
      placeholder="Search resoruces by name…"
      nameFilter={(resource, value) => resource.name.toLowerCase().includes(value)}
      renderRow={(resource) => (
        <SearchableListRow
          iconName="resource"
          label={resource.name}
          path={workspacePathFromAddress(repoAddress, `/resources/${resource.name}`)}
        />
      )}
    />
  );
};
