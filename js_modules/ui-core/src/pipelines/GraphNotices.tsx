import {
  Body2,
  Box,
  Button,
  Colors,
  MonoSmall,
  NonIdealState,
  Spinner,
} from '@dagster-io/ui-components';
import capitalize from 'lodash/capitalize';
import styled from 'styled-components';

import {SyntaxError} from '../selection/CustomErrorListener';

export const EmptyDAGNotice = ({
  isGraph,
  nodeType,
}: {
  isGraph: boolean;
  nodeType: 'asset' | 'op';
}) => {
  return (
    <CenteredContainer>
      <NonIdealState
        icon="no-results"
        title={isGraph ? 'Empty graph' : 'Empty job'}
        description={
          <div>
            This {isGraph ? 'graph' : 'job'} is empty. {capitalize(nodeType)}s will appear here when
            they are added to your definitions.
          </div>
        }
      />
    </CenteredContainer>
  );
};

export const EntirelyFilteredDAGNotice = ({nodeType}: {nodeType: 'asset' | 'op'}) => {
  return (
    <CenteredContainer>
      <NonIdealState
        icon="no-results"
        title="Nothing to display"
        description={
          <div>
            No {nodeType}s match your query filter. Try removing your filter, typing <code>*</code>{' '}
            to render the entire graph, or entering another filter string.
          </div>
        }
      />
    </CenteredContainer>
  );
};

export const InvalidSelectionQueryNotice = ({errors}: {errors: SyntaxError[]}) => {
  return (
    <CenteredContainer>
      <NonIdealState
        icon="no-results"
        title="Invalid selection query"
        description={
          <Box flex={{direction: 'column', gap: 8}}>
            The selection query you entered is invalid. Please try again.
            <MonoSmall>{errors.map((error) => error.message).join('\n')}</MonoSmall>
          </Box>
        }
      />
    </CenteredContainer>
  );
};

export const LoadingNotice = (props: {async: boolean; nodeType: 'asset' | 'op'}) => {
  const {async} = props;
  return (
    <LoadingContainer>
      {async ? (
        <Box margin={{bottom: 24}}>Rendering a large number of {props.nodeType}s, please wait…</Box>
      ) : null}
      <Spinner purpose="page" />
    </LoadingContainer>
  );
};

export const LoadingContainer = styled.div`
  background-color: ${Colors.backgroundDefault()};
  position: absolute;
  top: 57px;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 2;
`;

const CenteredContainer = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
`;

export const LargeDAGNotice = ({
  nodeType,
  setForceLargeGraph,
}: {
  nodeType: 'op' | 'asset';
  setForceLargeGraph: (enabled: boolean) => void;
}) => {
  return (
    <CenteredContainer>
      <NonIdealState
        icon="graph_vertical"
        title="This graph may be too large to display"
        description={
          <Box flex={{direction: 'column', gap: 16, alignItems: 'flex-start'}}>
            <Body2>
              Build an {nodeType} filter above to render a portion of the graph, or click below to
              attempt to render it in full.
            </Body2>
            <Button onClick={() => setForceLargeGraph(true)}>Show Graph</Button>
          </Box>
        }
      />
    </CenteredContainer>
  );
};

export const CycleDetectedNotice = () => {
  return (
    <CenteredContainer>
      <NonIdealState
        icon="error"
        title="Cycle detected"
        description={
          <div>
            This graph contains a cycle and cannot be displayed. Check your asset dependencies for
            circular references.
          </div>
        }
      />
    </CenteredContainer>
  );
};
