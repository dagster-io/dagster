import {gql, useQuery, useSubscription} from '@apollo/client';
import {Box, Colors, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {WebSocketContext} from '../app/WebSocketProvider';

import {RawLogContent} from './RawLogContent';
import {ILogCaptureInfo} from './RunMetadataProvider';
import {
  CapturedLogFragment,
  CapturedLogsMetadataQuery,
  CapturedLogsMetadataQueryVariables,
  CapturedLogsQuery,
  CapturedLogsQueryVariables,
  CapturedLogsSubscription,
  CapturedLogsSubscriptionVariables,
} from './types/CapturedLogPanel.types';

interface CapturedLogProps {
  logKey: string[];
  visibleIOType: string;
  onSetDownloadUrl?: (url: string) => void;
}

interface CapturedOrExternalLogPanelProps extends CapturedLogProps {
  logCaptureInfo?: ILogCaptureInfo;
}

export const CapturedOrExternalLogPanel: React.FC<CapturedOrExternalLogPanelProps> = React.memo(
  ({logCaptureInfo, ...props}) => {
    const externalUrl =
      logCaptureInfo &&
      (props.visibleIOType === 'stdout'
        ? logCaptureInfo.externalStdoutUrl
        : logCaptureInfo.externalStderrUrl);
    if (externalUrl) {
      return (
        <Box
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'center', gap: 1}}
          background={Colors.Gray900}
          style={{color: Colors.White, flex: 1, minHeight: 0}}
        >
          View logs at
          <a
            href={externalUrl}
            target="_blank"
            rel="noreferrer"
            style={{
              color: Colors.White,
              textDecoration: 'underline',
              marginLeft: 4,
              marginRight: 4,
            }}
          >
            {externalUrl}
          </a>
          <Icon name="open_in_new" color={Colors.White} size={20} style={{marginTop: 2}} />
        </Box>
      );
    }
    return props.logKey.length ? <CapturedLogPanel {...props} /> : null;
  },
);

const MAX_STREAMING_LOG_BYTES = 5242880; // 5 MB

const slice = (s: string) =>
  s.length < MAX_STREAMING_LOG_BYTES ? s : s.slice(-MAX_STREAMING_LOG_BYTES);

const merge = (a?: string | null, b?: string | null): string | null => {
  if (!b) {
    return a || null;
  }
  if (!a) {
    return slice(b);
  }
  return slice(a + b);
};

interface State {
  stdout: string | null;
  stderr: string | null;
  cursor?: string | null;
  isLoading: boolean;
  stdoutDownloadUrl?: string;
  stdoutLocation?: string;
  stderrDownloadUrl?: string;
  stderrLocation?: string;
}

type Action =
  | {type: 'update'; logData: CapturedLogFragment}
  | {type: 'metadata'; metadata: any}
  | {type: 'reset'};

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'update':
      return {
        ...state,
        isLoading: false,
        cursor: action.logData?.cursor,
        stdout: merge(state.stdout, action.logData?.stdout),
        stderr: merge(state.stderr, action.logData?.stderr),
      };
    case 'metadata':
      return {
        ...state,
        ...action.metadata,
      };
    case 'reset':
      return {
        ...initialState,
      };
    default:
      return state;
  }
};

const initialState: State = {
  stdout: null,
  stderr: null,
  cursor: null,
  isLoading: true,
};

const CapturedLogSubscription: React.FC<{
  logKey: string[];
  onLogData: (logData: CapturedLogFragment) => void;
}> = React.memo(({logKey, onLogData}) => {
  useSubscription<CapturedLogsSubscription, CapturedLogsSubscriptionVariables>(
    CAPTURED_LOGS_SUBSCRIPTION,
    {
      fetchPolicy: 'no-cache',
      variables: {logKey},
      onSubscriptionData: ({subscriptionData}) => {
        if (subscriptionData.data?.capturedLogs) {
          onLogData(subscriptionData.data.capturedLogs);
        }
      },
    },
  );
  return null;
});

const CAPTURED_LOGS_SUBSCRIPTION = gql`
  subscription CapturedLogsSubscription($logKey: [String!]!, $cursor: String) {
    capturedLogs(logKey: $logKey, cursor: $cursor) {
      ...CapturedLog
    }
  }

  fragment CapturedLog on CapturedLogs {
    stdout
    stderr
    cursor
  }
`;

const CAPTURED_LOGS_METADATA_QUERY = gql`
  query CapturedLogsMetadataQuery($logKey: [String!]!) {
    capturedLogsMetadata(logKey: $logKey) {
      stdoutDownloadUrl
      stdoutLocation
      stderrDownloadUrl
      stderrLocation
    }
  }
`;

const QUERY_LOG_LIMIT = 100000;
const POLL_INTERVAL = 5000;

const CapturedLogsSubscriptionProvider = ({
  logKey,
  children,
}: {
  logKey: string[];
  children: (result: State) => React.ReactChild;
}) => {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const logKeyString = JSON.stringify(logKey);
  React.useEffect(() => {
    dispatch({type: 'reset'});
  }, [logKeyString]);

  const onLogData = React.useCallback((logData: CapturedLogFragment) => {
    dispatch({type: 'update', logData});
  }, []);
  return (
    <>
      <CapturedLogSubscription logKey={logKey} onLogData={onLogData} />
      {children(state)}
    </>
  );
};

const CapturedLogsQueryProvider = ({
  logKey,
  children,
}: {
  logKey: string[];
  children: (result: State) => React.ReactChild;
}) => {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const logKeyString = JSON.stringify(logKey);
  React.useEffect(() => {
    dispatch({type: 'reset'});
  }, [logKeyString]);
  const {cursor} = state;

  const {stopPolling, startPolling} = useQuery<CapturedLogsQuery, CapturedLogsQueryVariables>(
    CAPTURED_LOGS_QUERY,
    {
      notifyOnNetworkStatusChange: true,
      variables: {logKey, cursor, limit: QUERY_LOG_LIMIT},
      pollInterval: POLL_INTERVAL,
      onCompleted: (data: CapturedLogsQuery) => {
        // We have to stop polling in order to update the `after` value.
        stopPolling();
        dispatch({type: 'update', logData: data.capturedLogs});
        startPolling(POLL_INTERVAL);
      },
    },
  );

  return <>{children(state)}</>;
};

const CAPTURED_LOGS_QUERY = gql`
  query CapturedLogsQuery($logKey: [String!]!, $cursor: String, $limit: Int) {
    capturedLogs(logKey: $logKey, cursor: $cursor, limit: $limit) {
      stdout
      stderr
      cursor
    }
  }
`;

const CapturedLogPanel: React.FC<CapturedLogProps> = React.memo(
  ({logKey, visibleIOType, onSetDownloadUrl}) => {
    const {rootServerURI} = React.useContext(AppContext);
    const {availability, disabled} = React.useContext(WebSocketContext);
    const queryResult = useQuery<CapturedLogsMetadataQuery, CapturedLogsMetadataQueryVariables>(
      CAPTURED_LOGS_METADATA_QUERY,
      {
        variables: {logKey},
      },
    );

    React.useEffect(() => {
      if (!onSetDownloadUrl || !queryResult.data) {
        return;
      }
      const visibleDownloadUrl =
        visibleIOType === 'stdout'
          ? queryResult.data.capturedLogsMetadata.stdoutDownloadUrl
          : queryResult.data.capturedLogsMetadata.stderrDownloadUrl;

      if (!visibleDownloadUrl) {
        return;
      }
      if (visibleDownloadUrl.startsWith('/')) {
        onSetDownloadUrl(rootServerURI + visibleDownloadUrl);
      } else {
        onSetDownloadUrl(visibleDownloadUrl);
      }
    }, [onSetDownloadUrl, visibleIOType, rootServerURI, queryResult.data]);

    const stdoutLocation = queryResult.data?.capturedLogsMetadata.stdoutLocation || undefined;
    const stderrLocation = queryResult.data?.capturedLogsMetadata.stderrLocation || undefined;
    const websocketsUnavailabile = availability === 'unavailable' || disabled;
    const Component = websocketsUnavailabile
      ? CapturedLogsQueryProvider
      : CapturedLogsSubscriptionProvider;
    return (
      <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column'}}>
        <Component logKey={logKey}>
          {(_state: State) => (
            <>
              <RawLogContent
                logData={_state.stdout}
                isLoading={_state.isLoading}
                location={stdoutLocation}
                isVisible={visibleIOType === 'stdout'}
              />
              <RawLogContent
                logData={_state.stderr}
                isLoading={_state.isLoading}
                location={stderrLocation}
                isVisible={visibleIOType === 'stderr'}
              />
            </>
          )}
        </Component>
      </div>
    );
  },
);
