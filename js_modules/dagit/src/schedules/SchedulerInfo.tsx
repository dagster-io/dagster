import {Callout, Code, Intent} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';

import PythonErrorInfo from '../PythonErrorInfo';

import {SchedulerFragment} from './types/SchedulerFragment';

export const SCHEDULER_FRAGMENT = gql`
  fragment SchedulerFragment on SchedulerOrError {
    __typename
    ... on SchedulerNotDefinedError {
      message
    }
    ... on Scheduler {
      schedulerClass
    }
    ...PythonErrorFragment
  }

  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;

export const SchedulerInfo: React.FunctionComponent<{
  errorsOnly?: boolean;
  schedulerOrError: SchedulerFragment;
}> = ({errorsOnly = false, schedulerOrError}) => {
  if (schedulerOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={schedulerOrError} />;
  }

  if (schedulerOrError.__typename === 'SchedulerNotDefinedError') {
    return (
      <Callout
        icon="time"
        intent={Intent.WARNING}
        title="The current dagster instance does not have a scheduler configured."
        style={{marginBottom: 40}}
      >
        <p>
          A scheduler must be configured on the instance to run schedules. Therefore, the schedules
          below are not currently running. You can configure a scheduler on the instance through the{' '}
          <Code>dagster.yaml</Code> file in <Code>$DAGSTER_HOME</Code>
        </p>

        <p>
          See the{' '}
          <a href="https://docs.dagster.io/overview/instances/dagster-instance#instance-configuration-yaml">
            instance configuration documentation
          </a>{' '}
          for more information.
        </p>
      </Callout>
    );
  }

  if (!errorsOnly && schedulerOrError.__typename === 'Scheduler') {
    return (
      <Callout icon="time" style={{marginBottom: 40}}>
        <span style={{fontWeight: 'bold'}}>Scheduler Class:</span>{' '}
        <pre style={{display: 'inline'}}>{schedulerOrError.schedulerClass}</pre>
      </Callout>
    );
  }

  return null;
};
