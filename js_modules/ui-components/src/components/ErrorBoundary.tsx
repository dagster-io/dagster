import * as React from 'react';

import {Box} from './Box';
import {Colors} from './Color';
import {Heading, Text} from './Typography';
import styles from './css/ErrorBoundary.module.css';

export type ErrorCollectionContextValue = {
  errorStackIncluded: boolean;
  errorCollectionMessage: string;
  onReportError: (error: Error, context: Record<string, unknown>) => void;
};

export const ErrorCollectionContext = React.createContext<ErrorCollectionContextValue>({
  errorStackIncluded: true,
  errorCollectionMessage:
    `Please report this error to the Dagster team via GitHub or Slack. ` +
    `Refresh the page to try again.`,
  onReportError: (error, context) => {
    console.error(error, context);
  },
});

interface ErrorBoundaryProps {
  children: React.ReactNode;
  region: string;
  resetErrorOnChange?: unknown[];
}

interface ErrorBoundaryState {
  error: Error | null;
  errorResetPropsValue: string | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {error: null, errorResetPropsValue: null};

  static contextType = ErrorCollectionContext;

  componentDidUpdate() {
    if (
      this.state.error &&
      this.state.errorResetPropsValue !== JSON.stringify(this.props.resetErrorOnChange)
    ) {
      this.setState({error: null, errorResetPropsValue: null});
    }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    if (typeof jest !== 'undefined') {
      throw error;
    }
    (this.context as ErrorCollectionContextValue).onReportError(error, {
      info,
      region: this.props.region,
    });
    this.setState({error, errorResetPropsValue: JSON.stringify(this.props.resetErrorOnChange)});
  }

  render() {
    const {error} = this.state;
    const {errorCollectionMessage, errorStackIncluded} = this
      .context as ErrorCollectionContextValue;

    if (error) {
      return (
        <Box
          style={{width: '100%', height: '100%', flex: 1, overflow: 'hidden'}}
          border={{side: 'all', color: Colors.accentRed()}}
          flex={{direction: 'column', gap: 8}}
          padding={16}
        >
          <Heading size={14} weight={600}>
            Sorry, {this.props.region} can&apos;t be displayed.
          </Heading>
          <Text size={14} color="textLight">
            {errorCollectionMessage}
          </Text>
          {errorStackIncluded && (
            <div className={styles.trace}>{`${error.message}\n\n${error.stack}`}</div>
          )}
        </Box>
      );
    }

    return this.props.children;
  }
}
