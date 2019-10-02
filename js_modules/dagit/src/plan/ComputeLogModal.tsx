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

  const close = () => setOpen(false);
  return (
    <>
      <LogLink onClick={() => setOpen(true)}>{children}</LogLink>
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
      {({ isLoading, computeLogs }) => {
        if (isLoading || !computeLogs) {
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
            computeLogs={computeLogs}
          />
        );
      }}
    </ComputeLogsProvider>
  );
};

interface IComputeLogsProviderProps {
  children: (props: {
    isLoading: boolean;
    computeLogs: ComputeLogsSubscriptionFragment | null;
  }) => React.ReactChild;
  runId: string;
  stepKey: string;
}
interface IComputeLogsProviderState {
  computeLogs: ComputeLogsSubscriptionFragment | null;
  isLoading: boolean;
}

export class ComputeLogsProvider extends React.Component<
  IComputeLogsProviderProps,
  IComputeLogsProviderState
> {
  static fragments = {
    subscription: gql`
      fragment ComputeLogsSubscriptionFragment on ComputeLogs {
        ...ComputeLogContentFragment
        stdout {
          data
        }
        stderr {
          data
        }
        cursor
      }
      ${ComputeLogContent.fragments.ComputeLogContentFragment}
    `
  };

  _subscription: DirectGraphQLSubscription<ComputeLogsSubscription>;
  state: IComputeLogsProviderState = { computeLogs: null, isLoading: true };

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
    this._subscription = new DirectGraphQLSubscription<ComputeLogsSubscription>(
      COMPUTE_LOGS_SUBSCRIPTION,
      { runId, stepKey, cursor: null },
      this.onMessages
    );
  }

  unsubscribe() {
    if (this._subscription) {
      this._subscription.close();
    }
  }

  onMessages = (
    messages: ComputeLogsSubscription[],
    _isFirstResponse: boolean
  ) => {
    let { computeLogs } = this.state;
    messages.forEach((subscription: ComputeLogsSubscription) => {
      if (!computeLogs) {
        computeLogs = subscription.computeLogs;
      } else {
        computeLogs = this.merge(computeLogs, subscription.computeLogs);
      }
    });
    this.setState({ computeLogs, isLoading: false });
  };

  merge(
    a: ComputeLogsSubscriptionFragment,
    b: ComputeLogsSubscriptionFragment
  ) {
    return {
      __typename: b.__typename,
      cursor: b.cursor,
      stdout: this.mergeFile(a.stdout, b.stdout),
      stderr: this.mergeFile(a.stderr, b.stderr)
    };
  }

  mergeFile(
    a: ComputeLogContentFileFragment | null,
    b: ComputeLogContentFileFragment | null
  ) {
    if (!a) return b;
    if (!b) return a;
    return {
      __typename: b.__typename,
      path: b.path,
      downloadUrl: b.downloadUrl,
      data: a.data + b.data
    };
  }

  render() {
    const { isLoading, computeLogs } = this.state;
    return this.props.children({ isLoading, computeLogs });
  }
}

const COMPUTE_LOGS_SUBSCRIPTION = gql`
  subscription ComputeLogsSubscription(
    $runId: ID!
    $stepKey: String!
    $cursor: String
  ) {
    computeLogs(runId: $runId, stepKey: $stepKey, cursor: $cursor) {
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
