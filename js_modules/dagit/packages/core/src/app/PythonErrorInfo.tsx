import {gql} from '@apollo/client';
import {Button, Icon, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {MetadataEntries} from '../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntryFragment';
import {ErrorSource} from '../types/globalTypes';

import {
  PythonErrorFragment,
  PythonErrorFragment_causes as Cause,
} from './types/PythonErrorFragment';

export type GenericError = {
  message: string;
  stack?: string[];
  causes?: Cause[];
};

interface IPythonErrorInfoProps {
  showReload?: boolean;
  centered?: boolean;
  error: GenericError | PythonErrorFragment;
  failureMetadata?: {metadataEntries: MetadataEntryFragment[]} | null;
  errorSource?: ErrorSource | null;
}

export const PythonErrorInfo: React.FC<IPythonErrorInfoProps> = (props) => {
  const {message, stack = [], causes = []} = props.error;

  const Wrapper = props.centered ? ErrorWrapperCentered : ErrorWrapper;
  const context = props.errorSource ? <ErrorContext errorSource={props.errorSource} /> : null;
  const metadataEntries = props.failureMetadata?.metadataEntries;

  return (
    <>
      {context}
      <Wrapper>
        <ErrorHeader>{message}</ErrorHeader>
        {metadataEntries ? (
          <div style={{marginTop: 10, marginBottom: 10}}>
            <MetadataEntries entries={metadataEntries} />
          </div>
        ) : null}
        {stack ? <Trace>{stack.join('')}</Trace> : null}
        {causes.map((cause, ii) => (
          <React.Fragment key={ii}>
            <CauseHeader>The above exception was caused by the following exception:</CauseHeader>
            <ErrorHeader>{cause.message}</ErrorHeader>
            {stack ? <Trace>{cause.stack.join('')}</Trace> : null}
          </React.Fragment>
        ))}
        {props.showReload && (
          <Button icon={<Icon name="refresh" />} onClick={() => window.location.reload()}>
            Reload
          </Button>
        )}
      </Wrapper>
    </>
  );
};

const ErrorContext: React.FC<{errorSource: ErrorSource}> = ({errorSource}) => {
  switch (errorSource) {
    case ErrorSource.UNEXPECTED_ERROR:
      return (
        <ContextHeader>An unexpected exception was thrown. Please file an issue.</ContextHeader>
      );
    default:
      return null;
  }
};

export const UNAUTHORIZED_ERROR_FRAGMENT = gql`
  fragment UnauthorizedErrorFragment on UnauthorizedError {
    message
  }
`;

export const PYTHON_ERROR_FRAGMENT = gql`
  fragment PythonErrorFragment on PythonError {
    __typename
    message
    stack
    causes {
      message
      stack
    }
  }
`;

const ContextHeader = styled.h4`
  font-weight: 400;
  margin: 0 0 1em;
`;

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
  font-size: 1em;
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
