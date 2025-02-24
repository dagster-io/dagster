import {
  BodySmall,
  Box,
  Colors,
  Icon,
  MiddleTruncate,
  MonoSmall,
  PopoverContentStyle,
  PopoverWrapperStyle,
} from '@dagster-io/ui-components';
import {useLayoutEffect, useMemo, useState} from 'react';
import ReactDOM from 'react-dom';
import styled from 'styled-components';

import {SyntaxError} from './CustomErrorListener';
import {applyStaticSyntaxHighlighting} from './SelectionInputHighlighter';
import {useUpdatingRef} from '../hooks/useUpdatingRef';

export const useSelectionInputLintingAndHighlighting = ({
  cmInstance,
  value,
  linter,
}: {
  cmInstance: React.MutableRefObject<CodeMirror.Editor | null>;
  value: string;
  linter: (content: string) => SyntaxError[];
}) => {
  const errors = useMemo(() => {
    const errors = linter(value);
    return errors.map((error, idx) => ({
      ...error,
      idx,
    }));
  }, [linter, value]);

  useLayoutEffect(() => {
    if (!cmInstance.current) {
      return;
    }
    applyStaticSyntaxHighlighting(cmInstance.current, errors);
  }, [cmInstance, errors]);

  const errorsRef = useUpdatingRef(errors);

  const [error, setError] = useState<{
    error: SyntaxError;
    x: number;
    y: number;
  } | null>(null);

  const errorRef = useUpdatingRef(error);

  useLayoutEffect(() => {
    const listener = (ev: MouseEvent) => {
      if (!(ev.target instanceof HTMLElement)) {
        return;
      }
      const error = ev.target.closest('.selection-input-error') as HTMLElement | null;
      if (error) {
        const regex = /selection-input-error-(\d+)/;
        const errorIdx = parseInt(error.className.match(regex)?.[1] ?? '0', 10);
        const errorAnnotation = errorsRef.current[errorIdx];
        if (errorAnnotation) {
          setError({
            error: errorAnnotation,
            x: ev.clientX,
            y: ev.clientY,
          });
          return;
        }
      }
      if (errorRef.current) {
        setError(null);
      }
    };
    document.body.addEventListener('mousemove', listener);
    return () => {
      document.body.removeEventListener('mousemove', listener);
    };
  }, [cmInstance, errorsRef, errorRef]);

  const message = useMemo(() => {
    if (!error) {
      return null;
    }
    if (error.error.offendingSymbol) {
      return (
        <Box flex={{direction: 'row', alignItems: 'center'}}>
          Unexpected input
          <div style={{width: 4}} />
          <MonoSmall color={Colors.textRed()}>
            <div style={{maxWidth: 200}}>
              <MiddleTruncate text={error.error.offendingSymbol} />
            </div>
          </MonoSmall>
          .
        </Box>
      );
    }
    if (error.error.message) {
      return error.error.message;
    }
    return null;
  }, [error]);

  if (!error) {
    return null;
  }

  return ReactDOM.createPortal(
    <PortalElement $bottom={error.y} $left={error.x}>
      <Box
        as={Content}
        padding={{horizontal: 12, vertical: 8}}
        flex={{direction: 'row', gap: 4}}
        color={Colors.textLight()}
      >
        <Icon name="run_failed" color={Colors.accentRed()} />
        <BodySmall color={Colors.textLight()}>{message}</BodySmall>
      </Box>
    </PortalElement>,
    document.body,
  );
};

const PortalElement = styled.div<{$bottom: number; $left: number}>`
  position: absolute;
  top: ${({$bottom}) => $bottom - 32}px;
  left: ${({$left}) => $left + 16}px;
  max-width: 600px;
  z-index: 20; // Z-index 20 to match bp5-overlay
  ${PopoverWrapperStyle}
`;

const Content = styled.div`
  ${PopoverContentStyle}
`;
