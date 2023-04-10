import React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {Colors} from './Colors';
import {Body, Subheading} from './Text';
import {FontFamily} from './styles';

export type ErrorCollectionContextValue = {
  errorStackIncluded: boolean;
  errorCollectionMessage: string;
  onReportError: (error: Error, context: Record<string, any>) => void;
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
  resetErrorOnChange?: any[];
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

  componentDidCatch(error: Error, info: any) {
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
          border={{width: 1, side: 'all', color: Colors.HighlightRed}}
          flex={{direction: 'column', gap: 8}}
          padding={16}
        >
          <Subheading>Sorry, {this.props.region} can&apos;t be displayed.</Subheading>
          <Body color={Colors.Gray700}>{errorCollectionMessage}</Body>
          {errorStackIncluded && <Trace>{`${error.message}\n\n${error.stack}`}</Trace>}
        </Box>
      );
    }

    return this.props.children;
  }
}

const Trace = styled.div`
  color: ${Colors.Gray700};
  font-family: ${FontFamily.monospace};
  font-size: 1em;
  white-space: pre;
  padding-bottom: 1em;
`;
