import {gql, useQuery, useSubscription} from '@apollo/client';
import {Box, Colors, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {RawLogContent} from './RawLogContent';
import {AppContext} from './app/AppContext';
import {
  CapturedLogsSubscription,
  CapturedLogsSubscriptionVariables,
  CapturedLogsSubscription_capturedLogs,
} from './types/CapturedLogsSubscription';

interface CapturedLogProps {
  logKey: string[];
  visibleIOType: string;
  onSetDownloadUrl?: (url: string) => void;
}

interface CapturedOrExternalLogPanelProps extends CapturedLogProps {
  externalUrl?: string;
}

export const CapturedOrExternalLogPanel: React.FC<CapturedOrExternalLogPanelProps> = React.memo(
  ({externalUrl, ...props}) => {
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

export const CapturedLogPanel: React.FC<CapturedLogProps> = React.memo(
  ({logKey, visibleIOType, onSetDownloadUrl}) => {
    const {rootServerURI} = React.useContext(AppContext);
    const [state, dispatch] = React.useReducer(reducer, initialState);

    const logKeyString = JSON.stringify(logKey);
    React.useEffect(() => {
      dispatch({type: 'reset'});
    }, [logKeyString]);

    const queryResult = useQuery(CAPTURED_LOGS_METADATA_QUERY, {
      variables: {logKey},
      fetchPolicy: 'cache-and-network',
    });

    React.useEffect(() => {
      if (queryResult.data) {
        dispatch({type: 'metadata', metadata: queryResult.data.capturedLogsMetadata});
      }
    }, [queryResult.data]);

    const {
      isLoading,
      stdout,
      stderr,
      stdoutLocation,
      stderrLocation,
      stderrDownloadUrl,
      stdoutDownloadUrl,
    } = state;

    React.useEffect(() => {
      const visibleDownloadUrl = visibleIOType === 'stdout' ? stdoutDownloadUrl : stderrDownloadUrl;
      if (!onSetDownloadUrl || !visibleDownloadUrl) {
        return;
      }
      if (visibleDownloadUrl.startsWith('/')) {
        onSetDownloadUrl(rootServerURI + visibleDownloadUrl);
      } else {
        onSetDownloadUrl(visibleDownloadUrl);
      }
    }, [onSetDownloadUrl, visibleIOType, stderrDownloadUrl, stdoutDownloadUrl, rootServerURI]);

    const onLogData = React.useCallback((logData: CapturedLogsSubscription_capturedLogs) => {
      dispatch({type: 'update', logData});
    }, []);

    return (
      <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column'}}>
        <CapturedLogSubscription logKey={logKey} onLogData={onLogData} />
        <RawLogContent
          logData={stdout}
          isLoading={isLoading}
          location={stdoutLocation}
          isVisible={visibleIOType === 'stdout'}
        />
        <RawLogContent
          logData={stderr}
          isLoading={isLoading}
          location={stderrLocation}
          isVisible={visibleIOType === 'stderr'}
        />
      </div>
    );
  },
);

export const MAX_STREAMING_LOG_BYTES = 5242880; // 5 MB

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
  | {type: 'update'; logData: CapturedLogsSubscription_capturedLogs}
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
  onLogData: (logData: CapturedLogsSubscription_capturedLogs) => void;
}> = React.memo(({logKey, onLogData}) => {
  // const counter = React.useRef(0);
  // const logKeyStr = JSON.stringify(logKey);
  // React.useEffect(() => {
  //   console.log(`Subscribed to ${logKeyStr}`);
  //   return () => console.log(`Unsubscribed from ${logKeyStr} after ${counter.current} messages`);
  // }, [logKeyStr]);

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
      stdout
      stderr
      cursor
    }
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
