import {Box, Colors, Icon, NonIdealState, Spinner} from '@dagster-io/ui';
import capitalize from 'lodash/capitalize';
import * as React from 'react';
import styled from 'styled-components/macro';

export const LargeDAGNotice = ({nodeType}: {nodeType: 'op' | 'asset'}) => (
  <LargeDAGContainer>
    <Icon name="arrow_upward" size={24} />
    <LargeDAGInstructionBox>
      <p>
        This is a large DAG that may be difficult to visualize. Type <code>*</code> in the graph
        filter bar to render the entire thing, or type {nodeType} names and use:
      </p>
      <ul style={{marginBottom: 0}}>
        <li>
          <code>+</code> to expand a single layer before or after the {nodeType}.
        </li>
        <li>
          <code>*</code> to expand recursively before or after the {nodeType}.
        </li>
        <li>
          <code>AND</code> to render another disconnected fragment.
        </li>
      </ul>
    </LargeDAGInstructionBox>
  </LargeDAGContainer>
);

export const EmptyDAGNotice: React.FC<{isGraph: boolean; nodeType: 'asset' | 'op'}> = ({
  isGraph,
  nodeType,
}) => {
  return (
    <CenteredContainer>
      <NonIdealState
        icon="no-results"
        title={isGraph ? 'Empty graph' : 'Empty pipeline'}
        description={
          <div>
            This {isGraph ? 'graph' : 'pipeline'} is empty. {capitalize(nodeType)}s will appear here
            when they are added to loaded repositories.
          </div>
        }
      />
    </CenteredContainer>
  );
};

export const EntirelyFilteredDAGNotice: React.FC<{nodeType: 'asset' | 'op'}> = ({nodeType}) => {
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

export const LoadingNotice: React.FC<{async: boolean; nodeType: 'asset' | 'op'}> = (props) => {
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

const LoadingContainer = styled.div`
  background-color: ${Colors.White};
  position: absolute;
  top: 0;
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

const LargeDAGContainer = styled.div`
  width: 45vw;
  position: absolute;
  left: 40px;
  top: 60px;
  z-index: 2;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  [role='img'] {
    opacity: 0.5;
    margin-left: 10vw;
  }
`;

const LargeDAGInstructionBox = styled.div`
  padding: 15px 20px;
  border: 1px solid #fff5c3;
  margin-top: 20px;
  color: ${Colors.Gray800};
  background: #fffbe5;
  text-align: left;
  line-height: 1.4rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  code {
    background: #f8ebad;
    font-weight: 500;
    padding: 0 4px;
  }
`;
