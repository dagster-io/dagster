import {ServerError} from '@apollo/client';
import {ErrorResponse, onError} from '@apollo/client/link/error';
import {Observable} from '@apollo/client/utilities';
import {Colors, FontFamily, Toaster} from '@dagster-io/ui-components';
import {GraphQLError} from 'graphql';
import memoize from 'lodash/memoize';

import {showCustomAlert} from './CustomAlertProvider';
import {ERROR_CODES_TO_SURFACE, errorCodeToMessage} from './HTTPErrorCodes';

interface DagsterSerializableErrorInfo {
  message: string;
  stack: string[];
  cls_name: string | null;
  cause: DagsterSerializableErrorInfo | null;
  context: DagsterSerializableErrorInfo | null;
}

type DagsterGraphQLError = GraphQLError & {
  extensions:
    | {
        errorInfo?: DagsterSerializableErrorInfo;
      }
    | undefined;
};

const getErrorToaster = memoize(async () => {
  return await Toaster.asyncCreate({position: 'top-right'}, document.body);
});

const showGraphQLError = async (error: DagsterGraphQLError, operationName?: string) => {
  const message = (
    <div>
      Unexpected GraphQL error
      <AppStackTraceLink error={error} operationName={operationName} />
    </div>
  );
  const toaster = await getErrorToaster();
  toaster.show({message, intent: 'danger'});
  console.error('[GraphQL error]', error);
};

const showNetworkError = async (statusCode: number) => {
  if (ERROR_CODES_TO_SURFACE.has(statusCode)) {
    const message = errorCodeToMessage(statusCode);
    const toaster = await getErrorToaster();
    toaster.show({message, intent: 'warning'});
  }
};

export const errorLink = onError((response: ErrorResponse) => {
  if (response.graphQLErrors) {
    const {graphQLErrors, operation} = response;
    const {operationName} = operation;
    graphQLErrors.forEach((error) => showGraphQLError(error as DagsterGraphQLError, operationName));
  }
  if (response.networkError) {
    // if we have a network error but there is still graphql data
    // the payload should contain a meaningful error for the product to handle
    const serverError = response.networkError as ServerError;
    if (serverError.result && serverError.result.data) {
      // we can return an observable here (normally used to perform retries)
      // to flow the error payload to the product
      return Observable.from([serverError.result]);
    }

    if (response.networkError && 'statusCode' in response.networkError) {
      showNetworkError(response.networkError.statusCode);
    }
    console.error('[Network error]', response.networkError);
  }
  return;
});

interface AppStackTraceLinkProps {
  error: DagsterGraphQLError;
  operationName?: string;
}

export const AppStackTraceLink = ({error, operationName}: AppStackTraceLinkProps) => {
  const title = 'Error';
  const stackTrace = error?.extensions?.errorInfo?.stack;
  const cause = error?.extensions?.errorInfo?.cause;
  const stackTraceContent = stackTrace ? (
    <>
      {'\n\n'}
      Stack Trace:
      {'\n'}
      {stackTrace.join('')}
    </>
  ) : null;
  const causeContent = cause ? (
    <>
      {'\n'}
      The above exception was the direct cause of the following exception:
      {'\n\n'}
      Message: {cause.message}
      {'\n\n'}
      Stack Trace:
      {'\n'}
      {cause.stack.join('')}
    </>
  ) : null;
  const instructions = (
    <div
      style={{
        fontFamily: FontFamily.default,
        fontSize: 16,
        marginBottom: 30,
      }}
    >
      You hit an unexpected error while fetching data from Dagster.
      <br />
      <br />
      If you have a minute, consider reporting this error either by{' '}
      <a href="https://github.com/dagster-io/dagster/issues/" rel="noreferrer" target="_blank">
        filing a Github issue
      </a>{' '}
      or by{' '}
      <a href="https://dagster.slack.com/archives/CCCR6P2UR" rel="noreferrer" target="_blank">
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
          backgroundColor: Colors.backgroundRed(),
          border: `1px solid ${Colors.accentRed()}`,
          borderRadius: 3,
          maxWidth: '90vw',
          maxHeight: '80vh',
          padding: '1em 2em',
          overflow: 'auto',
          color: Colors.textDefault(),
          fontFamily: FontFamily.monospace,
          fontSize: '1em',
          whiteSpace: 'pre',
          overflowX: 'auto',
        }}
      >
        {operationName ? `Operation name: ${operationName}\n\n` : null}
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

const IGNORED_CONSOLE_ERRORS = [
  'The above error occurred',
  'NetworkError when attempting to fetch resource',
  "Can't perform a React state update on an unmounted component",
];

export const setupErrorToasts = () => {
  const original = console.error;
  Object.defineProperty(console, 'error', {
    value: (...args: any[]) => {
      original.apply(console, args);

      const msg = `${args[0]}`;
      if (!IGNORED_CONSOLE_ERRORS.some((ignored) => msg.includes(ignored))) {
        // If the console.error happens during render, then our ErrorToaster.show call
        // will trigger the "Can't re-render component during render" console error
        // which would send us in an infinite loop. So we use setTimeout to avoid this.
        setTimeout(async () => {
          const toaster = await getErrorToaster();
          toaster.show({
            intent: 'danger',
            message: (
              <div
                style={{whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'hidden'}}
              >{`console.error: ${msg}`}</div>
            ),
          });
        }, 0);
      }
    },
  });

  window.addEventListener('unhandledrejection', async (event) => {
    (await getErrorToaster()).show({
      intent: 'danger',
      message: (
        <div
          style={{whiteSpace: 'pre-wrap'}}
        >{`Unhandled Rejection: ${event.reason}\nView console for details.`}</div>
      ),
    });
  });
};
