import {useQuery} from '@apollo/client';
import {Button, Callout, Intent, NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React, {useState} from 'react';

import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {ScheduleRow, ScheduleStateRow} from 'src/schedules/ScheduleRow';
import {SCHEDULES_ROOT_QUERY, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {RepositorySchedulesFragment} from 'src/schedules/types/RepositorySchedulesFragment';
import {ScheduleStatesFragment_results} from 'src/schedules/types/ScheduleStatesFragment';
import {SchedulesRootQuery} from 'src/schedules/types/SchedulesRootQuery';
import {Group} from 'src/ui/Group';
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
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: 50 * 1000,
    partialRefetch: true,
  });

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {(result) => {
        const {repositoryOrError, scheduler, unLoadableScheduleStates} = result;
        let scheduleDefinitionsSection = null;
        let unLoadableSchedulesSection = null;

        if (repositoryOrError.__typename === 'PythonError') {
          scheduleDefinitionsSection = <PythonErrorInfo error={repositoryOrError} />;
        } else if (unLoadableScheduleStates.__typename === 'PythonError') {
          scheduleDefinitionsSection = <PythonErrorInfo error={unLoadableScheduleStates} />;
        } else if (
          repositoryOrError.__typename === 'RepositoryNotFoundError' ||
          unLoadableScheduleStates.__typename === 'RepositoryNotFoundError'
        ) {
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
          unLoadableSchedulesSection = unLoadableScheduleStates.results.length > 0 && (
            <UnLoadableSchedules unLoadableSchedules={unLoadableScheduleStates.results} />
          );
        }

        return (
          <Group direction="vertical" spacing={20}>
            <SchedulerInfo schedulerOrError={scheduler} />
            {scheduleDefinitionsSection}
            {unLoadableSchedulesSection}
          </Group>
        );
      }}
    </Loading>
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

export interface UnloadableSchedulesProps {
  unLoadableSchedules: ScheduleStatesFragment_results[];
}

export const UnLoadableSchedules: React.FunctionComponent<UnloadableSchedulesProps> = (props) => {
  const {unLoadableSchedules} = props;

  return (
    <>
      <h3 style={{marginTop: 20}}>Unloadable schedules:</h3>
      <UnloadableScheduleInfo />

      <Table striped style={{width: '100%'}}>
        <thead>
          <tr>
            <th style={{maxWidth: '60px'}}></th>
            <th>Schedule Name</th>
            <th style={{width: '150px'}}>Schedule</th>
            <th style={{width: '100px'}}>Last Tick</th>
            <th>Latest Runs</th>
          </tr>
        </thead>
        <tbody>
          {unLoadableSchedules.map((scheduleState) => (
            <ScheduleStateRow
              scheduleState={scheduleState}
              key={scheduleState.scheduleOriginId}
              showStatus={true}
            />
          ))}
        </tbody>
      </Table>
    </>
  );
};

export const UnloadableScheduleInfo = () => {
  const [showMore, setShowMore] = useState(false);

  return (
    <Callout style={{marginBottom: 20}} intent={Intent.WARNING}>
      <div style={{display: 'flex', justifyContent: 'space-between'}}>
        <h4 style={{margin: 0}}>
          Note: You can turn off any of the following schedules, but you cannot turn them back on.{' '}
        </h4>

        {!showMore && (
          <Button small={true} onClick={() => setShowMore(true)}>
            Show more info
          </Button>
        )}
      </div>

      {showMore && (
        <div style={{marginTop: 10}}>
          <p>
            The following schedules were previously started but now cannot be loaded. They may be
            part of a different workspace or from a schedule or repository that no longer exists in
            code. You can turn them off, but you cannot turn them back on since they can’t be
            loaded.
          </p>
        </div>
      )}
    </Callout>
  );
};
