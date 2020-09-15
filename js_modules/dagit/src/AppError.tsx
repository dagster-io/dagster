import * as React from 'react';
import {Toaster, Position, Intent} from '@blueprintjs/core';
import {ErrorResponse, onError} from 'apollo-link-error';
import {GraphQLError} from 'graphql';
import {showCustomAlert} from './CustomAlertProvider';

export interface DagsterGraphQLError extends GraphQLError {
  stack_trace: string[];
  cause?: DagsterGraphQLError;
}
interface DagsterErrorResponse extends ErrorResponse {
  graphQLErrors?: ReadonlyArray<DagsterGraphQLError>;
}

const ErrorToaster = Toaster.create({position: Position.TOP_RIGHT});

export const showGraphQLError = (error: DagsterGraphQLError) => {
  const message = (
    <div>
      Unexpected GraphQL error
      <AppStackTraceLink error={error} />
    </div>
  );
  ErrorToaster.show({message, intent: Intent.DANGER});
  console.error('[GraphQL error]', error);
};

export const AppErrorLink = () => {
  return onError((response: DagsterErrorResponse) => {
    if (response.graphQLErrors) {
      response.graphQLErrors.forEach((error) => showGraphQLError(error));
    }
    if (response.networkError) {
      ErrorToaster.show({
        message: `[Network error] ${response.networkError.message}`,
        intent: Intent.DANGER,
      });
      console.error('[Network error]', response.networkError);
    }
  });
};

const AppStackTraceLink = ({error}: {error: DagsterGraphQLError}) => {
  const title = 'Error';
  const stackTraceContent = error.stack_trace ? (
    <>
      {'\n\n'}
      Stack Trace:
      {'\n'}
      {error.stack_trace.join('')}
    </>
  ) : null;
  const causeContent = error.cause ? (
    <>
      {'\n'}
      The above exception was the direct cause of the following exception:
      {'\n\n'}
      Message: {error.cause.message}
      {'\n\n'}
      Stack Trace:
      {'\n'}
      {error.cause.stack_trace.join('')}
    </>
  ) : null;
  const instructions = (
    <div
      style={{
        fontFamily: 'Open Sans, sans-serif',
        fontSize: 16,
        marginBottom: 30,
      }}
    >
      You hit an unexpected error while fetching data from Dagster.
      <br />
      <br />
      If you have a minute, consider reporting this error either by{' '}
      <a
        href="https://github.com/dagster-io/dagster/issues/"
        rel="noopener noreferrer"
        target="_blank"
      >
        filing a Github issue
      </a>{' '}
      or by{' '}
      <a
        href="https://dagster.slack.com/archives/CCCR6P2UR"
        rel="noopener noreferrer"
        target="_blank"
      >
        messaging in the Dagster slack
      </a>
      . Use the <code>&quot;Copy&quot;</code> button below to include error information that is
      helpful for the core development team to diagnose what is happening and to improve Dagster in
      recovering from unexpected errors.
    </div>
  );

  const body = (
    <div>
      {instructions}
      <div
        className="errorInfo"
        style={{
          backgroundColor: 'rgba(206, 17, 38, 0.05)',
          border: '1px solid #d17257',
          borderRadius: 3,
          maxWidth: '90vw',
          maxHeight: '80vh',
          padding: '1em 2em',
          overflow: 'auto',
          color: 'rgb(41, 50, 56)',
          fontFamily: 'Consolas, Menlo, monospace',
          fontSize: '0.85em',
          whiteSpace: 'pre',
          overflowX: 'auto',
        }}
      >
        Message: {error.message}
        {'\n\n'}
        Path: {JSON.stringify(error.path)}
        {'\n\n'}
        Locations: {JSON.stringify(error.locations)}
        {stackTraceContent}
        {causeContent}
      </div>
    </div>
  );

  return (
    <span
      style={{cursor: 'pointer', textDecoration: 'underline', marginLeft: 30}}
      onClick={() => showCustomAlert({title, body, copySelector: '.errorInfo'})}
    >
      View error info
    </span>
  );
};
