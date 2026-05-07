import {BodySmall, Box, Colors, Icon} from '@dagster-io/ui-components';
import debounce from 'lodash/debounce';
import {useCallback, useLayoutEffect, useMemo, useRef, useState} from 'react';
import ReactDOM from 'react-dom';

import {SyntaxError} from './CustomErrorListener';
import {applyStaticSyntaxHighlighting} from './SelectionInputHighlighter';
import styles from './css/useSelectionInputLintingAndHighlighting.module.css';
import {useUpdatingRef} from '../hooks/useUpdatingRef';

const EMPTY_ERRORS: SyntaxError[] = [];

export const useSelectionInputLintingAndHighlighting = ({
  cmInstance,
  linter,
  suppressErrors,
}: {
  cmInstance: React.MutableRefObject<CodeMirror.Editor | null>;
  linter: (content: string) => SyntaxError[];
  // When true, skip all validation errors. Used while the user is choosing a
  // value in the autocomplete dropdown — the in-progress expression would
  // otherwise flag errors on the unfinished token and everything after it.
  suppressErrors?: boolean;
}) => {
  const instance = cmInstance.current;

  const errorsRef = useRef<SyntaxError[]>([]);

  const lintErrors = useMemo(() => {
    const debouncedApplyErrors = debounce(() => {
      const instance = cmInstance.current;
      if (!instance) {
        return;
      }
      errorsRef.current = suppressErrors ? EMPTY_ERRORS : linter(instance.getValue());
      applyStaticSyntaxHighlighting(instance, errorsRef.current);
    }, 1000);

    return () => {
      const instance = cmInstance.current;
      if (!instance) {
        return;
      }
      const errors = suppressErrors ? EMPTY_ERRORS : linter(instance.getValue());
      if (!errors.length) {
        errorsRef.current = errors;
        applyStaticSyntaxHighlighting(instance, errors);
      } else {
        // Only debounce if there are errors to apply
        debouncedApplyErrors();
      }
    };
  }, [linter, cmInstance, suppressErrors]);

  const highlighter = useCallback(
    (instance: CodeMirror.Editor) => {
      lintErrors();
      applyStaticSyntaxHighlighting(instance, errorsRef.current);
    },
    [errorsRef, lintErrors],
  );

  useLayoutEffect(() => {
    if (!instance) {
      return;
    }
    instance.on('change', highlighter);
    highlighter(instance);
    return () => {
      instance.off('change', highlighter);
    };
  }, [highlighter, instance]);

  // Re-apply highlighting when suppression toggles so squiggles appear/
  // disappear as the autocomplete dropdown opens and closes, even if the
  // editor content hasn't changed.
  useLayoutEffect(() => {
    if (instance) {
      highlighter(instance);
    }
  }, [suppressErrors, highlighter, instance]);

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
    <div
      className={styles.portalElement}
      style={{
        top: error.y - 32,
        left: error.x + 16,
      }}
    >
      <div className={styles.content}>
        <Box padding={{horizontal: 12, vertical: 8}} flex={{direction: 'row', gap: 4}}>
          <Icon name="run_failed" color={Colors.accentRed()} />
          <BodySmall color={Colors.textLight()}>{message}</BodySmall>
        </Box>
      </div>
    </div>,
    document.body,
  );
};
