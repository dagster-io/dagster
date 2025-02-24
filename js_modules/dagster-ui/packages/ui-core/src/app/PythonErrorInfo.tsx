import {Box, Button, Colors, FontFamily, Icon} from '@dagster-io/ui-components';
import {Fragment, useRef} from 'react';
import {PythonErrorInfoHeader} from 'shared/app/PythonErrorInfoHeader.oss';
import {SummarizeErrorWithAIButton} from 'shared/runs/SummarizeErrorWithAIButton.oss';
import styled from 'styled-components';

import {showSharedToaster} from './DomUtils';
import {useCopyToClipboard} from './browser';
import {gql} from '../apollo-client';
import {PythonErrorChainFragment, PythonErrorFragment} from './types/PythonErrorFragment.types';
import {ErrorSource} from '../graphql/types';
import {MetadataEntries} from '../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntryFragment.types';

export type GenericError = {
  message: string;
  stack?: string[];
  errorChain?: PythonErrorChainFragment[];
};

interface IPythonErrorInfoProps {
  showReload?: boolean;
  centered?: boolean;
  error: GenericError | PythonErrorFragment;
  failureMetadata?: {metadataEntries: MetadataEntryFragment[]} | null;
  errorSource?: ErrorSource | null;
}

export const PythonErrorInfo = (props: IPythonErrorInfoProps) => {
  const {message, stack = [], errorChain = []} = props.error;

  const Wrapper = props.centered ? ErrorWrapperCentered : ErrorWrapper;
  const context = props.errorSource ? <ErrorContext errorSource={props.errorSource} /> : null;
  const metadataEntries = props.failureMetadata?.metadataEntries;
  const copy = useCopyToClipboard();

  const wrapperRef = useRef<HTMLDivElement | null>(null);

  return (
    <>
      {PythonErrorInfoHeader ? (
        <PythonErrorInfoHeader error={props.error} fallback={context} />
      ) : (
        context
      )}
      <Wrapper ref={wrapperRef}>
        <Box flex={{direction: 'row', gap: 6, alignItems: 'center', justifyContent: 'flex-end'}}>
          <SummarizeErrorWithAIButton error={props.error} />
          <CopyErrorButton
            copy={() => {
              const text = wrapperRef.current?.innerText || '';
              copy(text.slice(5)); // Strip the word "Copy"
            }}
          />
        </Box>
        <ErrorHeader>{message}</ErrorHeader>
        {metadataEntries ? (
          <div style={{marginTop: 10, marginBottom: 10}}>
            <MetadataEntries entries={metadataEntries} />
          </div>
        ) : null}
        {stack ? <Trace>{stack.join('')}</Trace> : null}
        {errorChain.map((chainLink, ii) => (
          <Fragment key={ii}>
            <CauseHeader>
              {chainLink.isExplicitLink
                ? 'The above exception was caused by the following exception:'
                : 'The above exception occurred during handling of the following exception:'}
            </CauseHeader>
            <ErrorHeader>{chainLink.error.message}</ErrorHeader>
            {stack ? <Trace>{chainLink.error.stack.join('')}</Trace> : null}
          </Fragment>
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

const ErrorContext = ({errorSource}: {errorSource: ErrorSource}) => {
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

export const CopyErrorButton = ({copy}: {copy: () => void | string}) => {
  return (
    <Button
      outlined
      onClick={async () => {
        const message = copy();
        await showSharedToaster({
          message: message ?? <div>Copied value</div>,
          intent: 'success',
        });
      }}
      icon={<Icon name="content_copy" />}
    >
      Copy
    </Button>
  );
};

const ContextHeader = styled.h4`
  font-weight: 400;
  margin: 0 0 1em;
`;

const CauseHeader = styled.h3`
  font-weight: 400;
  margin: 1em 0 1em;
`;

const ErrorHeader = styled.h3`
  color: ${Colors.textRed()};
  font-weight: 400;
  margin: 0.5em 0 0.25em;
  white-space: pre-wrap;
`;

const Trace = styled.div`
  color: ${Colors.textLight()};
  font-family: ${FontFamily.monospace};
  font-size: 12px;
  font-variant-ligatures: none;
  white-space: pre;
  padding-bottom: 1em;
`;

export const ErrorWrapper = styled.div`
  background-color: ${Colors.backgroundRed()};
  border: 1px solid ${Colors.accentRed()};
  border-radius: 3px;
  max-width: 90vw;
  max-height: calc(100vh - 250px);
  padding: 1em 2em;
  overflow: auto;
`;

export const ErrorWrapperCentered = styled(ErrorWrapper)`
  position: absolute;
  left: 50%;
  top: 100px;
  transform: translate(-50%, 0);
`;
