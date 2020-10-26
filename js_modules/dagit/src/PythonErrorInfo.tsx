import {gql} from '@apollo/client';
import {Button} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {MetadataEntries} from 'src/runs/MetadataEntry';
import {MetadataEntryFragment} from 'src/runs/types/MetadataEntryFragment';
import {PythonErrorFragment} from 'src/types/PythonErrorFragment';
import {FontFamily} from 'src/ui/styles';

interface IPythonErrorInfoProps {
  showReload?: boolean;
  centered?: boolean;
  contextMsg?: string;
  error: {message: string} | PythonErrorFragment;
  failureMetadata?: {metadataEntries: MetadataEntryFragment[]} | null;
}

export class PythonErrorInfo extends React.Component<IPythonErrorInfoProps> {
  static fragments = {
    PythonErrorFragment: gql`
      fragment PythonErrorFragment on PythonError {
        __typename
        message
        stack
        cause {
          message
          stack
        }
      }
    `,
  };

  render() {
    const message = this.props.error.message;
    const stack = (this.props.error as PythonErrorFragment).stack;
    const cause = (this.props.error as PythonErrorFragment).cause;

    const Wrapper = this.props.centered ? ErrorWrapperCentered : ErrorWrapper;
    const context = this.props.contextMsg ? (
      <ErrorHeader>{this.props.contextMsg}</ErrorHeader>
    ) : null;
    const metadataEntries = this.props.failureMetadata?.metadataEntries;

    return (
      <Wrapper>
        {context}
        <ErrorHeader>{message}</ErrorHeader>
        {metadataEntries ? (
          <div style={{marginTop: 10, marginBottom: 10}}>
            <MetadataEntries entries={metadataEntries} />
          </div>
        ) : null}
        <Trace>{stack ? stack.join('') : 'No Stack Provided.'}</Trace>
        {cause ? (
          <>
            <CauseHeader>The above exception was caused by the following exception:</CauseHeader>
            <ErrorHeader>{cause.message}</ErrorHeader>
            <Trace>{cause.stack ? cause.stack.join('') : 'No Stack Provided.'}</Trace>
          </>
        ) : null}
        {this.props.showReload && (
          <Button icon="refresh" onClick={() => window.location.reload()}>
            Reload
          </Button>
        )}
      </Wrapper>
    );
  }
}

const CauseHeader = styled.h3`
  font-weight: 400;
  margin: 1em 0 1em;
`;

const ErrorHeader = styled.h3`
  color: #b05c47;
  font-weight: 400;
  margin: 0.5em 0 0.25em;
`;

const Trace = styled.div`
  color: rgb(41, 50, 56);
  font-family: ${FontFamily.monospace};
  font-size: 0.85em;
  white-space: pre;
  padding-bottom: 1em;
`;

const ErrorWrapper = styled.div`
  background-color: #fdf2f4;
  border: 1px solid #d17257;
  border-radius: 3px;
  max-width: 90vw;
  max-height: calc(100vh - 250px);
  padding: 1em 2em;
  overflow: auto;
`;

const ErrorWrapperCentered = styled(ErrorWrapper)`
  position: absolute;
  left: 50%;
  top: 100px;
  transform: translate(-50%, 0);
`;
