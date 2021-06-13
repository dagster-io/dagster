import {gql} from '@apollo/client';
import * as React from 'react';

import {DirectGraphQLSubscription} from '../app/DirectGraphQLSubscription';
import {ComputeIOType} from '../types/globalTypes';

import {COMPUTE_LOG_CONTENT_FRAGMENT, MAX_STREAMING_LOG_BYTES} from './ComputeLogContent';
import {ComputeLogContentFileFragment} from './types/ComputeLogContentFileFragment';
import {ComputeLogsSubscription} from './types/ComputeLogsSubscription';
import {ComputeLogsSubscriptionFragment} from './types/ComputeLogsSubscriptionFragment';

interface IComputeLogsProviderProps {
  children: (props: {
    isLoading: boolean;
    stdout: ComputeLogsSubscriptionFragment | null;
    stderr: ComputeLogsSubscriptionFragment | null;
  }) => React.ReactChild;
  runId: string;
  stepKey: string;
  websocketURI: string;
}
interface IComputeLogsProviderState {
  stdout: ComputeLogsSubscriptionFragment | null;
  stderr: ComputeLogsSubscriptionFragment | null;
  isLoading: boolean;
}

export class ComputeLogsProvider extends React.Component<
  IComputeLogsProviderProps,
  IComputeLogsProviderState
> {
  _stdout: DirectGraphQLSubscription<ComputeLogsSubscription> | null = null;
  _stderr: DirectGraphQLSubscription<ComputeLogsSubscription> | null = null;
  state: IComputeLogsProviderState = {
    stdout: null,
    stderr: null,
    isLoading: true,
  };

  componentDidMount() {
    this.subscribe();
  }

  componentWillUnmount() {
    this.unsubscribe();
  }

  componentDidUpdate(prevProps: IComputeLogsProviderProps) {
    if (prevProps.runId !== this.props.runId || prevProps.stepKey !== this.props.stepKey) {
      this.unsubscribe();
      this.subscribe();
    }
  }

  subscribe() {
    const {runId, stepKey} = this.props;
    this.setState({isLoading: true, stdout: null, stderr: null});
    this._stdout = new DirectGraphQLSubscription<ComputeLogsSubscription>(
      this.props.websocketURI,
      COMPUTE_LOGS_SUBSCRIPTION,
      {runId, stepKey, ioType: ComputeIOType.STDOUT, cursor: null},
      this.onStdout,
      this.onError,
    );
    this._stderr = new DirectGraphQLSubscription<ComputeLogsSubscription>(
      this.props.websocketURI,
      COMPUTE_LOGS_SUBSCRIPTION,
      {runId, stepKey, ioType: ComputeIOType.STDERR, cursor: null},
      this.onStderr,
      this.onError,
    );
  }

  unsubscribe() {
    if (this._stdout) {
      this._stdout.close();
    }
    if (this._stderr) {
      this._stderr.close();
    }
  }

  onStdout = (messages: ComputeLogsSubscription[], _: boolean) => {
    this.onMessages('stdout', messages);
  };

  onStderr = (messages: ComputeLogsSubscription[], _: boolean) => {
    this.onMessages('stderr', messages);
  };

  onMessages = (ioType: string, messages: ComputeLogsSubscription[]) => {
    let computeLogs = this.state[ioType];
    messages.forEach((subscription: ComputeLogsSubscription) => {
      computeLogs = this.merge(computeLogs, subscription.computeLogs);
    });

    if (ioType === 'stdout') {
      this.setState({stdout: computeLogs, isLoading: false});
    } else {
      this.setState({stderr: computeLogs, isLoading: false});
    }
  };

  onError = () => {
    this.setState({isLoading: false});
  };

  merge(a: ComputeLogContentFileFragment | null, b: ComputeLogContentFileFragment | null) {
    if (!b) {
      return a;
    }
    let data = a?.data;
    if (a?.data && b?.data) {
      data = this.slice(a.data + b.data);
    } else if (b?.data) {
      data = this.slice(b.data);
    }
    return {
      __typename: b.__typename,
      path: b.path,
      downloadUrl: b.downloadUrl,
      data: data,
      cursor: b.cursor,
    };
  }

  slice(s: string) {
    if (s.length < MAX_STREAMING_LOG_BYTES) {
      return s;
    }
    return s.slice(-MAX_STREAMING_LOG_BYTES);
  }

  render() {
    const {isLoading, stdout, stderr} = this.state;
    return this.props.children({isLoading, stdout, stderr});
  }
}

const COMPUTE_LOGS_SUBSCRIPTION_FRAGMENT = gql`
  fragment ComputeLogsSubscriptionFragment on ComputeLogFile {
    data
    cursor
    ...ComputeLogContentFileFragment
  }
  ${COMPUTE_LOG_CONTENT_FRAGMENT}
`;

const COMPUTE_LOGS_SUBSCRIPTION = gql`
  subscription ComputeLogsSubscription(
    $runId: ID!
    $stepKey: String!
    $ioType: ComputeIOType!
    $cursor: String
  ) {
    computeLogs(runId: $runId, stepKey: $stepKey, ioType: $ioType, cursor: $cursor) {
      ...ComputeLogsSubscriptionFragment
    }
  }
  ${COMPUTE_LOGS_SUBSCRIPTION_FRAGMENT}
`;
