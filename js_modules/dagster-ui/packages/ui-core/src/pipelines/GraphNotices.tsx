import {Box, Colors, NonIdealState, Spinner} from '@dagster-io/ui-components';
import capitalize from 'lodash/capitalize';
import styled from 'styled-components';

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
