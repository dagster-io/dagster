import {
  Callout,
  Card,
  Code,
  Colors,
  Intent,
  NonIdealState,
  PopoverInteractionKind,
  Tooltip,
} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {useQuery} from 'react-apollo';

import {useRepositorySelector} from 'src/DagsterRepositoryContext';
import {Header, Legend, LegendColumn, ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RepositoryInformation} from 'src/RepositoryInformation';
import {ReconcileButton} from 'src/schedules/ReconcileButton';
import {ScheduleRow, ScheduleStateRow} from 'src/schedules/ScheduleRow';
import {SCHEDULES_ROOT_QUERY, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {
  SchedulesRootQuery,
  SchedulesRootQuery_repositoryOrError_Repository,
  SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results,
  SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results,
} from 'src/schedules/types/SchedulesRootQuery';

const GetStaleReconcileSection: React.FunctionComponent<{
  scheduleDefinitionsWithoutState: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results[];
  scheduleStatesWithoutDefinitions: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results[];
}> = ({scheduleDefinitionsWithoutState, scheduleStatesWithoutDefinitions}) => {
  if (
    scheduleDefinitionsWithoutState.length === 0 &&
    scheduleStatesWithoutDefinitions.length === 0
  ) {
    return null;
  }

  return (
    <Card style={{backgroundColor: Colors.LIGHT_GRAY4}}>
      <Callout intent={Intent.WARNING}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <p>
              There have been changes to the list of schedule definitions in this repository since
              the last time the scheduler state had been reconciled. For the dagster scheduler to
              run schedules, schedule definitions need to be reconciled with the internal schedule
              storage database.
            </p>
            <p>
              To reconcile schedule state, run <Code>dagster schedule up</Code> or click{' '}
              <ReconcileButton />
            </p>
          </div>
        </div>
      </Callout>
      <ScheduleWithoutStateTable schedules={scheduleDefinitionsWithoutState} />
      <ScheduleStatesWithoutDefinitionsTable scheduleStates={scheduleStatesWithoutDefinitions} />
    </Card>
  );
};

export const SchedulesRoot: React.FunctionComponent = () => {
  const repositorySelector = useRepositorySelector();

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
        const {
          scheduler,
          repositoryOrError,
          scheduleDefinitionsOrError,
          scheduleStatesOrError: scheduleStatesWithoutDefinitionsOrError,
        } = result;
        let staleReconcileSection = null;
        let scheduleDefinitionsSection = null;

        if (scheduleDefinitionsOrError.__typename === 'PythonError') {
          scheduleDefinitionsSection = <PythonErrorInfo error={scheduleDefinitionsOrError} />;
        } else if (repositoryOrError.__typename === 'PythonError') {
          scheduleDefinitionsSection = <PythonErrorInfo error={repositoryOrError} />;
        } else if (repositoryOrError.__typename === 'RepositoryNotFoundError') {
          // Should not be possible, the schedule definitions call will error out
        } else if (scheduleDefinitionsOrError.__typename === 'ScheduleDefinitions') {
          const scheduleDefinitions = scheduleDefinitionsOrError.results;
          const scheduleDefinitionsWithState = scheduleDefinitions.filter((s) => s.scheduleState);
          const scheduleDefinitionsWithoutState = scheduleDefinitions.filter(
            (s) => !s.scheduleState,
          );

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
            scheduleDefinitionsSection = (
              <ScheduleTable
                schedules={scheduleDefinitionsWithState}
                repository={repositoryOrError}
              />
            );
          }

          if (scheduleStatesWithoutDefinitionsOrError.__typename === 'ScheduleStates') {
            const scheduleStatesWithoutDefinitions =
              scheduleStatesWithoutDefinitionsOrError.results;
            staleReconcileSection = (
              <GetStaleReconcileSection
                scheduleDefinitionsWithoutState={scheduleDefinitionsWithoutState}
                scheduleStatesWithoutDefinitions={scheduleStatesWithoutDefinitions}
              />
            );
          }
        }

        return (
          <ScrollContainer>
            <SchedulerInfo schedulerOrError={scheduler} errorsOnly={true} />
            {staleReconcileSection}
            {scheduleDefinitionsSection}
          </ScrollContainer>
        );
      }}
    </Loading>
  );
};

const ScheduleTable: React.FunctionComponent<{
  schedules: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results[];
  repository: SchedulesRootQuery_repositoryOrError_Repository;
}> = (props) => {
  if (props.schedules.length === 0) {
    return null;
  }

  return (
    <div>
      <div style={{display: 'flex'}}>
        <Header>Schedules</Header>
        <div style={{flex: 1}} />
        <SchedulerTimezoneNote />
      </div>
      <div>
        {`${props.schedules.length} loaded from `}
        <Tooltip
          interactionKind={PopoverInteractionKind.HOVER}
          content={
            <pre>
              <RepositoryInformation repository={props.repository} />
              <div style={{fontSize: 11}}>
                <span style={{marginRight: 5}}>id:</span>
                <span style={{opacity: 0.5}}>{props.repository.id}</span>
              </div>
            </pre>
          }
        >
          <Code>{props.repository.name}</Code>
        </Tooltip>
      </div>

      {props.schedules.length > 0 && (
        <Legend>
          <LegendColumn style={{maxWidth: 60, paddingRight: 2}}></LegendColumn>
          <LegendColumn style={{flex: 1.4}}>Schedule Name</LegendColumn>
          <LegendColumn>Pipeline</LegendColumn>
          <LegendColumn style={{maxWidth: 150}}>Schedule</LegendColumn>
          <LegendColumn style={{maxWidth: 100}}>Last Tick</LegendColumn>
          <LegendColumn style={{flex: 1}}>Latest Runs</LegendColumn>
          <LegendColumn style={{flex: 1}}>Execution Params</LegendColumn>
        </Legend>
      )}
      {props.schedules.map((schedule) => (
        <ScheduleRow schedule={schedule} key={schedule.name} />
      ))}
    </div>
  );
};

const ScheduleWithoutStateTable: React.FunctionComponent<{
  schedules: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results[];
}> = (props) => {
  if (props.schedules.length === 0) {
    return null;
  }

  return (
    <div style={{marginTop: 10, marginBottom: 10}}>
      <h4>New Schedule Definitions</h4>
      <p>
        The following are new schedule definitions for which there are no entries in schedule
        storage yet. After reconciliation, these schedules can be turned on.
      </p>
      {props.schedules.length > 0 && (
        <Legend>
          <LegendColumn style={{flex: 1.4}}>Schedule Name</LegendColumn>
          <LegendColumn>Pipeline</LegendColumn>
          <LegendColumn style={{maxWidth: 150}}>Schedule</LegendColumn>
          <LegendColumn style={{flex: 1}}>Execution Params</LegendColumn>
        </Legend>
      )}
      {props.schedules.map((schedule) => (
        <ScheduleRow schedule={schedule} key={schedule.name} />
      ))}
    </div>
  );
};

interface ScheduleStateTableProps {
  scheduleStates: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results[];
}

const ScheduleStatesWithoutDefinitionsTable: React.FunctionComponent<ScheduleStateTableProps> = (
  props,
) => {
  if (props.scheduleStates.length === 0) {
    return null;
  }

  return (
    <div style={{marginTop: 20, marginBottom: 10}}>
      <h4>Deleted Schedule Definitions</h4>
      <p>
        The following are entries in schedule storage for which there is no matching schedule
        definition anymore. This means that the schedule definition has been deleted or renamed.
        After reconciliation, these entries will be deleted.
      </p>
      {props.scheduleStates.length > 0 && (
        <Legend>
          <LegendColumn style={{flex: 1.4}}>Schedule Name</LegendColumn>
          <LegendColumn style={{maxWidth: 150}}>Schedule</LegendColumn>
          <LegendColumn style={{maxWidth: 100}}>Last Tick</LegendColumn>
          <LegendColumn style={{flex: 1}}>Latest Runs</LegendColumn>
        </Legend>
      )}
      {props.scheduleStates.map((scheduleState) => (
        <ScheduleStateRow scheduleState={scheduleState} key={scheduleState.scheduleOriginId} />
      ))}
    </div>
  );
};
