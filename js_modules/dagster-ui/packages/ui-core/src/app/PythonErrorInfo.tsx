import {Box, Button, Icon} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {Fragment, useRef} from 'react';
import {PythonErrorInfoHeader} from 'shared/app/PythonErrorInfoHeader.oss';
import {SummarizeErrorWithAIButton} from 'shared/runs/SummarizeErrorWithAIButton.oss';

import {showSharedToaster} from './DomUtils';
import {useCopyToClipboard} from './browser';
import {gql} from '../apollo-client';
import styles from './css/PythonErrorInfo.module.css';
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

  const wrapperClass = clsx(
    styles.errorWrapper,
    props.centered ? styles.errorWrapperCentered : null,
  );
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
      <div ref={wrapperRef} className={wrapperClass}>
        <Box flex={{direction: 'row', gap: 6, alignItems: 'center', justifyContent: 'flex-end'}}>
          <SummarizeErrorWithAIButton error={props.error} />
          <CopyErrorButton
            copy={() => {
              const text = wrapperRef.current?.innerText || '';
              copy(text.slice(5)); // Strip the word "Copy"
            }}
          />
        </Box>
        <h3 className={styles.errorHeader}>{message}</h3>
        {metadataEntries ? (
          <div style={{marginTop: 10, marginBottom: 10}}>
            <MetadataEntries entries={metadataEntries} />
          </div>
        ) : null}
        {stack ? <div className={styles.trace}>{stack.join('')}</div> : null}
        {errorChain.map((chainLink, ii) => (
          <Fragment key={ii}>
            <h3 className={styles.causeHeader}>
              {chainLink.isExplicitLink
                ? 'The above exception was caused by the following exception:'
                : 'The above exception occurred during handling of the following exception:'}
            </h3>
            <h3 className={styles.errorHeader}>{chainLink.error.message}</h3>
            {stack ? <div className={styles.trace}>{chainLink.error.stack.join('')}</div> : null}
          </Fragment>
        ))}
        {props.showReload && (
          <Button icon={<Icon name="refresh" />} onClick={() => window.location.reload()}>
            Reload
          </Button>
        )}
      </div>
    </>
  );
};

const ErrorContext = ({errorSource}: {errorSource: ErrorSource}) => {
  switch (errorSource) {
    case ErrorSource.UNEXPECTED_ERROR:
      return (
        <h4 className={styles.contextHeader}>
          An unexpected exception was thrown. Please file an issue.
        </h4>
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

export const ErrorWrapper = ({children}: {children: React.ReactNode}) => (
  <div className={styles.errorWrapper}>{children}</div>
);
