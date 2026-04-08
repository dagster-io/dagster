import {Body2, Box, Button, MonoSmall, NonIdealState, Spinner} from '@dagster-io/ui-components';
import clsx from 'clsx';
import capitalize from 'lodash/capitalize';
import * as React from 'react';

import {SyntaxError} from '../selection/CustomErrorListener';
import styles from './css/GraphNotices.module.css';

export const EmptyDAGNotice = ({
  isGraph,
  nodeType,
}: {
  isGraph: boolean;
  nodeType: 'asset' | 'op';
}) => {
  return (
    <div className={styles.centeredContainer}>
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
    </div>
  );
};

export const EntirelyFilteredDAGNotice = ({nodeType}: {nodeType: 'asset' | 'op'}) => {
  return (
    <div className={styles.centeredContainer}>
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
    </div>
  );
};

export const InvalidSelectionQueryNotice = ({errors}: {errors: SyntaxError[]}) => {
  return (
    <div className={styles.centeredContainer}>
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
    </div>
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

export const LargeDAGNotice = ({
  nodeType,
  setForceLargeGraph,
}: {
  nodeType: 'op' | 'asset';
  setForceLargeGraph: (enabled: boolean) => void;
}) => {
  return (
    <div className={styles.centeredContainer}>
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
    </div>
  );
};

export const CycleDetectedNotice = () => {
  return (
    <div className={styles.centeredContainer}>
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
    </div>
  );
};

export const LoadingContainer = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<'div'>
>((props, ref) => {
  return <div {...props} ref={ref} className={clsx(styles.loadingContainer, props.className)} />;
});
