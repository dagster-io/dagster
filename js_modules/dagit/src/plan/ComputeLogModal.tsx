import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Dialog, Spinner, Intent } from "@blueprintjs/core";
import { RunContext } from "../runs/RunContext";
import { IStepState } from "../RunMetadataProvider";
import { DirectGraphQLSubscription } from "../DirectGraphQLSubscription";
import { ComputeLogContent } from "./ComputeLogContent";
import { ComputeLogsSubscription } from "./types/ComputeLogsSubscription";
import { ComputeLogsSubscriptionFragment } from "./types/ComputeLogsSubscriptionFragment";
import { ComputeLogContentFileFragment } from "./types/ComputeLogContentFileFragment";
import { ComputeIOType } from "../types/globalTypes";

interface IComputeLogLink {
  children: React.ReactNode;
  runState: IStepState;
  stepKey: string;
}

export const ComputeLogLink = ({
  runState,
  stepKey,
  children
}: IComputeLogLink) => {
  const [isOpen, setOpen] = React.useState(false);
  const run = React.useContext(RunContext);

  if (
    !run ||
    !run.runId ||
    runState === IStepState.WAITING ||
    runState === IStepState.SKIPPED
  ) {
    return null;
  }

  const open = (e: React.SyntheticEvent) => {
    e.stopPropagation();
    setOpen(true);
  };
  const close = () => setOpen(false);

  return (
    <>
      <LogLink onClick={open}>{children}</LogLink>
      <Dialog
        onClose={close}
        style={{
          width: "100vw",
          height: "100vh",
          margin: 0,
          padding: 0,
          borderRadius: 0
        }}
        usePortal={true}
        isOpen={isOpen}
      >
        {isOpen ? (
          <ComputeLogModal
            runId={run.runId}
            runState={runState}
            stepKey={stepKey}
            onRequestClose={close}
          />
        ) : (
          <LoadingContainer>
            <Spinner intent={Intent.NONE} size={32} />
          </LoadingContainer>
        )}
      </Dialog>
    </>
  );
};

interface ComputeLogModalProps {
  runId: string;
  stepKey: string;
  runState: IStepState;
  onRequestClose: () => void;
}

export const ComputeLogModal = ({
  runId,
  onRequestClose,
  stepKey,
  runState
}: ComputeLogModalProps) => {
  return (
    <ComputeLogsProvider runId={runId} stepKey={stepKey}>
      {({ isLoading, stdout, stderr }) => {
        if (isLoading || !stdout || !stderr) {
          return (
            <LoadingContainer>
              <Spinner intent={Intent.NONE} size={32} />
            </LoadingContainer>
          );
        }

        return (
          <ComputeLogContent
            runState={runState}
            onRequestClose={onRequestClose}
            stdout={stdout}
            stderr={stderr}
          />
        );
      }}
    </ComputeLogsProvider>
  );
};

interface IComputeLogsProviderProps {
  children: (props: {
    isLoading: boolean;
    stdout: ComputeLogsSubscriptionFragment | null;
    stderr: ComputeLogsSubscriptionFragment | null;
  }) => React.ReactChild;
  runId: string;
  stepKey: string;
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
  static fragments = {
    subscription: gql`
      fragment ComputeLogsSubscriptionFragment on ComputeLogFile {
        data
        cursor
        ...ComputeLogContentFileFragment
      }
      ${ComputeLogContent.fragments.ComputeLogContentFragment}
    `
  };

  _stdout: DirectGraphQLSubscription<ComputeLogsSubscription>;
  _stderr: DirectGraphQLSubscription<ComputeLogsSubscription>;
  state: IComputeLogsProviderState = {
    stdout: null,
    stderr: null,
    isLoading: true
  };

  componentDidMount() {
    this.subscribe();
  }

  componentWillUnmount() {
    this.unsubscribe();
  }

  componentDidUpdate(prevProps: IComputeLogsProviderProps) {
    if (
      prevProps.runId !== this.props.runId ||
      prevProps.stepKey !== this.props.stepKey
    ) {
      this.unsubscribe();
      this.subscribe();
    }
  }

  subscribe() {
    const { runId, stepKey } = this.props;
    this.setState({ isLoading: true });
    this._stdout = new DirectGraphQLSubscription<ComputeLogsSubscription>(
      COMPUTE_LOGS_SUBSCRIPTION,
      { runId, stepKey, ioType: ComputeIOType.STDOUT, cursor: null },
      this.onStdout
    );
    this._stderr = new DirectGraphQLSubscription<ComputeLogsSubscription>(
      COMPUTE_LOGS_SUBSCRIPTION,
      { runId, stepKey, ioType: ComputeIOType.STDERR, cursor: null },
      this.onStderr
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

  onStdout = (
    messages: ComputeLogsSubscription[],
    _isFirstResponse: boolean
  ) => {
    this.onMessages("stdout", messages);
  };

  onStderr = (
    messages: ComputeLogsSubscription[],
    _isFirstResponse: boolean
  ) => {
    this.onMessages("stderr", messages);
  };

  onMessages = (ioType: string, messages: ComputeLogsSubscription[]) => {
    let computeLogs = this.state[ioType];
    messages.forEach((subscription: ComputeLogsSubscription) => {
      if (!computeLogs) {
        computeLogs = subscription.computeLogs;
      } else {
        computeLogs = this.merge(computeLogs, subscription.computeLogs);
      }
    });
    if (ioType === "stdout") {
      this.setState({ stdout: computeLogs, isLoading: false });
    } else {
      this.setState({ stderr: computeLogs, isLoading: false });
    }
  };

  merge(
    a: ComputeLogContentFileFragment | null,
    b: ComputeLogContentFileFragment | null
  ) {
    if (!a) return b;
    if (!b) return a;
    return {
      __typename: b.__typename,
      path: b.path,
      downloadUrl: b.downloadUrl,
      data: a.data + b.data,
      cursor: b.cursor
    };
  }

  render() {
    const { isLoading, stdout, stderr } = this.state;
    return this.props.children({ isLoading, stdout, stderr });
  }
}

const COMPUTE_LOGS_SUBSCRIPTION = gql`
  subscription ComputeLogsSubscription(
    $runId: ID!
    $stepKey: String!
    $ioType: ComputeIOType!
    $cursor: String
  ) {
    computeLogs(
      runId: $runId
      stepKey: $stepKey
      ioType: $ioType
      cursor: $cursor
    ) {
      ...ComputeLogsSubscriptionFragment
    }
  }
  ${ComputeLogsProvider.fragments.subscription}
`;

const LogLink = styled.a`
  margin-left: 10px;
`;
const LoadingContainer = styled.div`
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
`;
