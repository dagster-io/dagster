import {Box, Button, Icon} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {ComponentProps, Fragment, forwardRef, useRef} from 'react';
import {PythonErrorInfoHeader} from 'shared/app/PythonErrorInfoHeader.oss';

import {showSharedToaster} from './DomUtils';
import {useCopyToClipboard} from './browser';
import {ErrorSource} from '../graphql/types';
import {MetadataEntries} from '../metadata/MetadataEntry';
import styles from './css/PythonErrorInfo.module.css';
import {PythonErrorChainFragment, PythonErrorFragment} from './types/PythonErrorFragment.types';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntryFragment.types';

export type GenericError = {
  message: string;
  stack?: string[];
  errorChain?: PythonErrorChainFragment[];
};

interface IPythonErrorInfoProps {
  showReload?: boolean;
  error: GenericError | PythonErrorFragment;
  failureMetadata?: {metadataEntries: MetadataEntryFragment[]} | null;
  errorSource?: ErrorSource | null;
}

export const PythonErrorInfo = (props: IPythonErrorInfoProps) => {
  const {message, stack = [], errorChain = []} = props.error;

  const context = props.errorSource ? <ErrorContext errorSource={props.errorSource} /> : null;
  const metadataEntries = props.failureMetadata?.metadataEntries;
  const copy = useCopyToClipboard();

  const wrapperRef = useRef<HTMLDivElement | null>(null);

  return (
    <>
      <PythonErrorInfoHeader error={props.error} fallback={context} />
      <ErrorWrapper ref={wrapperRef}>
        <h3 className={styles.errorHeader}>{message}</h3>
        {metadataEntries ? (
          <Box margin={{vertical: 12}}>
            <MetadataEntries entries={metadataEntries} />
          </Box>
        ) : null}
        {stack ? <div className={styles.trace}>{stack.join('')}</div> : null}
        {errorChain.map((chainLink, ii) => {
          const {message, stack} = chainLink.error;
          return (
            <Fragment key={ii}>
              <h3 className={styles.causeHeader}>
                {chainLink.isExplicitLink
                  ? '上述异常由以下异常引起：'
                  : '在处理以下异常时发生了上述异常：'}
              </h3>
              <h3 className={styles.errorHeader}>{message}</h3>
              {stack ? <div className={styles.trace}>{stack.join('')}</div> : null}
            </Fragment>
          );
        })}
        {props.showReload && (
          <Button icon={<Icon name="refresh" />} onClick={() => window.location.reload()}>
            重新加载
          </Button>
        )}
        <Box
          border="top"
          margin={{top: 8}}
          padding={{top: 16}}
          flex={{direction: 'row', gap: 4, alignItems: 'center', justifyContent: 'flex-end'}}
        >
          <CopyErrorButton
            copy={() => {
              const text = wrapperRef.current?.innerText || '';
              copy(text.slice(0, -1 * '复制错误'.length)); // Strip "复制错误"
            }}
          />
        </Box>
      </ErrorWrapper>
    </>
  );
};

const ErrorContext = ({errorSource}: {errorSource: ErrorSource}) => {
  if (errorSource === ErrorSource.UNEXPECTED_ERROR) {
    return (
      <h4 className={styles.contextHeader}>
        发生意外异常。请提交问题报告。
      </h4>
    );
  }
  return null;
};

export const CopyErrorButton = ({copy}: {copy: () => void | string}) => {
  return (
    <Button
      outlined
      onClick={async () => {
        const message = copy();
        await showSharedToaster({
          message: message ?? <div>已复制</div>,
          intent: 'success',
        });
      }}
      icon={<Icon name="content_copy" />}
    >
      复制错误
    </Button>
  );
};

type ErrorWrapperProps = ComponentProps<typeof Box>;

export const ErrorWrapper = forwardRef<HTMLDivElement, ErrorWrapperProps>(
  ({className, ...rest}, ref) => {
    return <Box {...rest} ref={ref} padding={24} className={clsx(styles.wrapper, className)} />;
  },
);

ErrorWrapper.displayName = 'ErrorWrapper';
