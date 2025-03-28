import {
  BodySmall,
  Box,
  Colors,
  Icon,
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
  linter,
}: {
  cmInstance: React.MutableRefObject<CodeMirror.Editor | null>;
  linter: (content: string) => SyntaxError[];
}) => {
  const instance = cmInstance.current;

  const [errors, setErrors] = useState<SyntaxError[]>([]);
  const errorsRef = useUpdatingRef(errors);
  useLayoutEffect(() => {
    if (!instance) {
      return;
    }
    const callback = (instance: CodeMirror.Editor) => {
      const errors = linter(instance.getValue());
      setErrors(errors);
      applyStaticSyntaxHighlighting(instance, errors);
    };
    instance.on('change', callback);
    callback(instance);
    return () => {
      instance.off('change', callback);
    };
  }, [instance, linter]);

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
      const symbol = error.error.offendingSymbol;
      if (symbol === '<EOF>') {
        return 'Selection is incomplete';
      }
      return <Box flex={{direction: 'row', alignItems: 'center'}}>{error.error.message}</Box>;
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
