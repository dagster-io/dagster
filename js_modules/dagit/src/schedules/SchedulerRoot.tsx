import {gql, useQuery} from '@apollo/client';
import {Button, Callout, Code, Divider, IBreadcrumbProps, Icon, Intent} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React, {useState} from 'react';
import {Link} from 'react-router-dom';

import {ButtonLink} from 'src/ButtonLink';
import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RepositoryInformation} from 'src/RepositoryInformation';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';
import {ScheduleStateRow} from 'src/schedules/ScheduleRow';
import {SCHEDULE_STATE_FRAGMENT, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT, SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {
  SchedulerRootQuery,
  SchedulerRootQuery_scheduleStatesOrError,
  SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results,
} from 'src/schedules/types/SchedulerRootQuery';
import {Table} from 'src/ui/Table';
import {DagsterRepoOption, useRepositoryOptions} from 'src/workspace/WorkspaceContext';
import {workspacePath} from 'src/workspace/workspacePath';

type ScheduleState = SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results;

export const SchedulerRoot: React.FunctionComponent<{}> = () => {
  useDocumentTitle('Scheduler');
  const queryResult = useQuery<SchedulerRootQuery>(SCHEDULER_ROOT_QUERY, {
    variables: {},
    fetchPolicy: 'cache-and-network',
  });

  const breadcrumbs: IBreadcrumbProps[] = [{icon: 'time', text: 'Scheduler'}];

  return (
    <ScrollContainer>
      <TopNav breadcrumbs={breadcrumbs} />
      <div style={{padding: '16px'}}>
        <Loading queryResult={queryResult} allowStaleData={true}>
          {(result) => {
            const {scheduler, scheduleStatesOrError} = result;
            return (
              <>
                <SchedulerInfo schedulerOrError={scheduler} />
                <ScheduleStates scheduleStatesOrError={scheduleStatesOrError} />
              </>
            );
          }}
        </Loading>
      </div>
    </ScrollContainer>
  );
};

const UnloadableScheduleInfo: React.FunctionComponent<{}> = () => {
  const [showMore, setShowMore] = useState(false);

  return (
    <Callout style={{marginBottom: 20}} intent={Intent.WARNING}>
      <div style={{display: 'flex', justifyContent: 'space-between'}}>
        <h4 style={{margin: 0}}>
          Note: You can turn off any of following running schedules, but you cannot turn them back
          on.{' '}
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
            Each schedule below was been previously reconciled and stored, but its corresponding{' '}
            <Code>ScheduleDefinition</Code> is not available in any of the currently loaded
            repositories. This is most likely because the schedule definition belongs to a workspace
            different than the one currently loaded, or because the repository origin for the
            schedule definition has changed.
          </p>
        </div>
      )}
    </Callout>
  );
};

const RepositorySchedules = ({
  repositoryLoadableSchedules,
  repositoryOriginId,
  option,
}: {
  repositoryLoadableSchedules: ScheduleState[];
  repositoryOriginId: string;
  option: DagsterRepoOption;
}) => {
  const {repository} = option;

  const [showRepositoryOrigin, setShowRepositoryOrigin] = useState(false);

  return (
    <div key={repositoryOriginId} style={{marginTop: 30}}>
      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 20}}>
        <div style={{display: 'flex', alignItems: 'base'}}>
          <h3 style={{marginTop: 0, marginBottom: 0}}>Repository: {repository.name}</h3>
          <ButtonLink onClick={() => setShowRepositoryOrigin(!showRepositoryOrigin)}>
            show info{' '}
            <Icon icon={showRepositoryOrigin ? IconNames.CHEVRON_DOWN : IconNames.CHEVRON_RIGHT} />
          </ButtonLink>
        </div>
        <Link
          to={workspacePath(option.repository.name, option.repositoryLocation.name, '/schedules')}
        >
          Go to repository schedules
        </Link>
      </div>
      {showRepositoryOrigin && (
        <Callout style={{marginBottom: 20}}>
          <RepositoryInformation repository={repository} />
        </Callout>
      )}
      {repositoryLoadableSchedules.length ? (
        <Table striped style={{width: '100%'}}>
          <thead>
            <tr>
              <th style={{maxWidth: '60px'}}></th>
              <th style={{paddingLeft: '20px'}}>Schedule Name</th>
              <th style={{width: '150px'}}>Schedule</th>
              <th style={{width: '100px'}}>Last Tick</th>
              <th>Latest Runs</th>
            </tr>
          </thead>
          <tbody>
            {repositoryLoadableSchedules.map((scheduleState: any) => (
              <ScheduleStateRow
                scheduleState={scheduleState}
                key={scheduleState.scheduleOriginId}
                showStatus={true}
                dagsterRepoOption={option}
              />
            ))}
          </tbody>
        </Table>
      ) : null}
    </div>
  );
};

const ScheduleStates: React.FunctionComponent<{
  scheduleStatesOrError: SchedulerRootQuery_scheduleStatesOrError;
}> = ({scheduleStatesOrError}) => {
  const {options, error} = useRepositoryOptions();

  if (error) {
    return <PythonErrorInfo error={error} />;
  } else if (scheduleStatesOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={scheduleStatesOrError} />;
  } else if (scheduleStatesOrError.__typename === 'RepositoryNotFoundError') {
    // Can't reach this case because we didn't use a repository selector
    return null;
  }

  const {results: scheduleStates} = scheduleStatesOrError;

  // Build map of repositoryOriginId to DagsterRepoOption
  const repositoryOriginIdMap = {};
  for (const option of options) {
    repositoryOriginIdMap[option.repository.id] = option;
  }

  // Seperate out schedules into in-scope and out-of-scope
  const loadableSchedules = scheduleStates.filter(({repositoryOriginId}) =>
    repositoryOriginIdMap.hasOwnProperty(repositoryOriginId),
  );

  const unLoadableSchedules = scheduleStates.filter(
    ({repositoryOriginId}) => !repositoryOriginIdMap.hasOwnProperty(repositoryOriginId),
  );

  // Group loadable schedules by repository
  const loadableSchedulesByRepositoryOriginId: {
    [key: string]: ScheduleState[];
  } = {};
  for (const loadableSchedule of loadableSchedules) {
    const {repositoryOriginId} = loadableSchedule;
    if (!loadableSchedulesByRepositoryOriginId.hasOwnProperty(repositoryOriginId)) {
      loadableSchedulesByRepositoryOriginId[repositoryOriginId] = [];
    }

    loadableSchedulesByRepositoryOriginId[repositoryOriginId].push(loadableSchedule);
  }

  return (
    <div>
      <div style={{display: 'flex'}}>
        <h2 style={{marginBottom: 0}}>All Schedules:</h2>
        <div style={{flex: 1}} />
        <SchedulerTimezoneNote />
      </div>
      <Divider />

      {Object.entries(loadableSchedulesByRepositoryOriginId).map((item) => {
        const [repositoryOriginId, repositoryloadableSchedules]: [string, ScheduleState[]] = item;
        const option = repositoryOriginIdMap[repositoryOriginId];

        return (
          <RepositorySchedules
            key={repositoryOriginId}
            repositoryOriginId={repositoryOriginId}
            repositoryLoadableSchedules={repositoryloadableSchedules}
            option={option}
          />
        );
      })}

      {unLoadableSchedules.length > 0 && (
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
      )}
    </div>
  );
};

const SCHEDULER_ROOT_QUERY = gql`
  query SchedulerRootQuery {
    scheduler {
      ...SchedulerFragment
    }
    scheduleStatesOrError {
      ... on ScheduleStates {
        results {
          ...ScheduleStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${SCHEDULER_FRAGMENT}
  ${SCHEDULE_STATE_FRAGMENT}
`;
