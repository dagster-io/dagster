import {useQuery} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React from 'react';

import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {UnloadableJobs} from 'src/jobs/UnloadableJobs';
import {ScheduleRow} from 'src/schedules/ScheduleRow';
import {SCHEDULES_ROOT_QUERY, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {RepositorySchedulesFragment} from 'src/schedules/types/RepositorySchedulesFragment';
import {SchedulesRootQuery} from 'src/schedules/types/SchedulesRootQuery';
import {JobType} from 'src/types/globalTypes';
import {Group} from 'src/ui/Group';
import {Page} from 'src/ui/Page';
import {Table} from 'src/ui/Table';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

interface Props {
  repoAddress: RepoAddress;
}

export const SchedulesRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  useDocumentTitle('Schedules');
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<SchedulesRootQuery>(SCHEDULES_ROOT_QUERY, {
    variables: {
      repositorySelector: repositorySelector,
      jobType: JobType.SCHEDULE,
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: 50 * 1000,
    partialRefetch: true,
  });

  return (
    <Page>
      <Loading queryResult={queryResult} allowStaleData={true}>
        {(result) => {
          const {repositoryOrError, scheduler, unloadableJobStatesOrError} = result;
          let scheduleDefinitionsSection = null;
          let unloadableSchedulesSection = null;

          if (repositoryOrError.__typename === 'PythonError') {
            scheduleDefinitionsSection = <PythonErrorInfo error={repositoryOrError} />;
          } else if (unloadableJobStatesOrError.__typename === 'PythonError') {
            scheduleDefinitionsSection = <PythonErrorInfo error={unloadableJobStatesOrError} />;
          } else if (repositoryOrError.__typename === 'RepositoryNotFoundError') {
            scheduleDefinitionsSection = (
              <NonIdealState
                icon={IconNames.ERROR}
                title="Repository not found"
                description="Could not load this repository."
              />
            );
          } else {
            const scheduleDefinitions = repositoryOrError.scheduleDefinitions;
            if (!scheduleDefinitions.length) {
              scheduleDefinitionsSection = (
                <NonIdealState
                  icon={IconNames.ERROR}
                  title="No Schedules Found"
                  description={
                    <p>
                      This repository does not have any schedules defined. Visit the{' '}
                      <a href="https://docs.dagster.io/overview/scheduling-partitions/schedules">
                        scheduler documentation
                      </a>{' '}
                      for more information about scheduling pipeline runs in Dagster. .
                    </p>
                  }
                />
              );
            } else {
              scheduleDefinitionsSection = scheduleDefinitions.length > 0 && (
                <Group direction="vertical" spacing={16}>
                  <SchedulerTimezoneNote schedulerOrError={scheduler} />
                  <SchedulesTable repository={repositoryOrError} />
                </Group>
              );
            }
            unloadableSchedulesSection = unloadableJobStatesOrError.results.length > 0 && (
              <UnloadableJobs
                jobStates={unloadableJobStatesOrError.results}
                jobType={JobType.SCHEDULE}
              />
            );
          }

          return (
            <Group direction="vertical" spacing={20}>
              <SchedulerInfo schedulerOrError={scheduler} />
              {scheduleDefinitionsSection}
              {unloadableSchedulesSection}
            </Group>
          );
        }}
      </Loading>
    </Page>
  );
};

export interface SchedulesTableProps {
  repository: RepositorySchedulesFragment;
}

export const SchedulesTable: React.FunctionComponent<SchedulesTableProps> = (props) => {
  const {repository} = props;

  const repoAddress = {
    name: repository.name,
    location: repository.location.name,
  };
  const schedules = repository.scheduleDefinitions;

  return (
    <>
      <Table striped style={{width: '100%'}}>
        <thead>
          <tr>
            <th style={{maxWidth: '60px'}}></th>
            <th>Schedule Name</th>
            <th>Pipeline</th>
            <th style={{width: '150px'}}>Schedule</th>
            <th style={{width: '100px'}}>Last Tick</th>
            <th>Latest Runs</th>
            <th>Execution Params</th>
          </tr>
        </thead>
        <tbody>
          {schedules.map((schedule) => (
            <ScheduleRow repoAddress={repoAddress} schedule={schedule} key={schedule.name} />
          ))}
        </tbody>
      </Table>
    </>
  );
};
