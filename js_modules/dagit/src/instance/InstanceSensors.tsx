import {QueryResult} from '@apollo/client';
import * as React from 'react';

import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {InstanceHealthQuery} from 'src/instance/types/InstanceHealthQuery';
import {UnloadableSensors} from 'src/jobs/UnloadableJobs';
import {SensorInfo} from 'src/sensors/SensorInfo';
import {SensorsTable} from 'src/sensors/SensorsTable';
import {JobType} from 'src/types/globalTypes';
import {Group} from 'src/ui/Group';
import {Subheading} from 'src/ui/Text';

interface Props {
  queryData: QueryResult<InstanceHealthQuery>;
}

export const InstanceSensors = (props: Props) => {
  const {queryData} = props;

  return (
    <Loading queryResult={queryData} allowStaleData={true}>
      {(result) => {
        const {instance, repositoriesOrError, unloadableJobStatesOrError} = result;

        if (repositoriesOrError.__typename === 'PythonError') {
          return <PythonErrorInfo error={repositoriesOrError} />;
        }
        if (unloadableJobStatesOrError.__typename === 'PythonError') {
          return <PythonErrorInfo error={unloadableJobStatesOrError} />;
        }

        const unloadableJobs = unloadableJobStatesOrError.results;
        const withSensors = repositoriesOrError.nodes.filter(
          (repository) => repository.sensors.length,
        );

        const sensorDefinitionsSection = withSensors.length ? (
          <Group direction="column" spacing={32}>
            <SensorInfo daemonHealth={instance.daemonHealth} />
            {withSensors.map((repository) =>
              repository.sensors.length ? (
                <Group direction="column" spacing={12} key={repository.name}>
                  <Subheading>{`${repository.name}@${repository.location.name}`}</Subheading>
                  <SensorsTable
                    repoAddress={{name: repository.name, location: repository.location.name}}
                    sensors={repository.sensors}
                  />
                </Group>
              ) : null,
            )}
          </Group>
        ) : null;

        return (
          <Group direction="column" spacing={32}>
            {sensorDefinitionsSection}
            <UnloadableSensors
              sensorStates={unloadableJobs.filter((state) => state.jobType === JobType.SENSOR)}
            />
          </Group>
        );
      }}
    </Loading>
  );
};
