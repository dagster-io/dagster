import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {InstanceHealthFragment} from '../instance/types/InstanceHealthFragment';
import {UnloadableSensors} from '../jobs/UnloadableJobs';
import {JobType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Subheading} from '../ui/Text';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {SensorInfo} from './SensorInfo';
import {SensorsTable} from './SensorsTable';
import {AllSensorsRepositoriesFragment} from './types/AllSensorsRepositoriesFragment';
import {AllSensorsUnloadablesFragment} from './types/AllSensorsUnloadablesFragment';

interface Props {
  instance: InstanceHealthFragment;
  repositoriesOrError: AllSensorsRepositoriesFragment;
  unloadableJobStatesOrError: AllSensorsUnloadablesFragment;
}

export const AllSensors: React.FC<Props> = (props) => {
  const {instance, repositoriesOrError, unloadableJobStatesOrError} = props;

  if (repositoriesOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={repositoriesOrError} />;
  }
  if (unloadableJobStatesOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={unloadableJobStatesOrError} />;
  }

  const unloadableJobs = unloadableJobStatesOrError.results;
  const withSensors = repositoriesOrError.nodes.filter((repository) => repository.sensors.length);

  const sensorDefinitionsSection = withSensors.length ? (
    <Group direction="column" spacing={32}>
      <SensorInfo daemonHealth={instance.daemonHealth} />
      {withSensors.map((repository) =>
        repository.sensors.length ? (
          <Group direction="column" spacing={12} key={repository.name}>
            <Subheading>{`${repository.name}@${repository.location.name}`}</Subheading>
            <SensorsTable
              repoAddress={buildRepoAddress(repository.name, repository.location.name)}
              sensors={repository.sensors}
            />
          </Group>
        ) : null,
      )}
    </Group>
  ) : null;

  const unloadableSensors = unloadableJobs.filter((state) => state.jobType === JobType.SENSOR);
  const unloadableSensorsSection = unloadableSensors.length ? (
    <UnloadableSensors sensorStates={unloadableSensors} />
  ) : null;

  if (!sensorDefinitionsSection && !unloadableSensorsSection) {
    return (
      <Box margin={{top: 32}}>
        <NonIdealState
          icon="automatic-updates"
          title="No sensors found"
          description={
            <p>
              This instance does not have any sensors defined. Visit the{' '}
              <a
                href="https://docs.dagster.io/overview/schedules-sensors/sensors"
                target="_blank"
                rel="noreferrer"
              >
                sensor documentation
              </a>{' '}
              for more information about setting up sensors in Dagster.
            </p>
          }
        />
      </Box>
    );
  }

  return (
    <Group direction="column" spacing={32}>
      {sensorDefinitionsSection}
      {unloadableSensorsSection}
    </Group>
  );
};
