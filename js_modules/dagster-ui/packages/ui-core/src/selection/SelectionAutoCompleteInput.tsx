import {Colors, Icon} from '@dagster-io/ui-components';
import CodeMirror, {Editor, HintFunction} from 'codemirror';
import {Linter} from 'codemirror/addon/lint/lint';
import debounce from 'lodash/debounce';
import {useCallback, useLayoutEffect, useMemo, useRef} from 'react';
import styled, {createGlobalStyle, css} from 'styled-components';

import {
  SelectionAutoCompleteInputCSS,
  applyStaticSyntaxHighlighting,
} from './SelectionAutoCompleteHighlighter';
import {useTrackEvent} from '../app/analytics';
import {useUpdatingRef} from '../hooks/useUpdatingRef';
import {createSelectionHint} from '../selection/SelectionAutoComplete';

import 'codemirror/addon/edit/closebrackets';
import 'codemirror/lib/codemirror.css';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';
import 'codemirror/addon/lint/lint.css';
import 'codemirror/addon/display/placeholder';

type SelectionAutoCompleteInputProps<T extends Record<string, string[]>, N extends keyof T> = {
  id: string; // Used for logging
  nameBase: N;
  attributesMap: T;
  placeholder: string;
  functions: string[];
  linter: Linter<any>;
  value: string;
  onChange: (value: string) => void;
};

export const SelectionAutoCompleteInput = <T extends Record<string, string[]>, N extends keyof T>({
  id,
  value,
  nameBase,
  placeholder,
  onChange,
  functions,
  linter,
  attributesMap,
}: SelectionAutoCompleteInputProps<T, N>) => {
  const trackEvent = useTrackEvent();

  const trackSelection = useMemo(() => {
    return debounce((selection: string) => {
      const selectionLowerCase = selection.toLowerCase();
      const hasBooleanLogic =
        selectionLowerCase.includes(' or ') ||
        selectionLowerCase.includes(' and ') ||
        selectionLowerCase.includes(' not ') ||
        selectionLowerCase.startsWith('not ');
      trackEvent(`${id}-selection-query`, {
        selection,
        booleanLogic: hasBooleanLogic,
      });
    }, 5000);
  }, [trackEvent, id]);

  const onSelectionChange = useCallback(
    (selection: string) => {
      onChange(selection);
      trackSelection(selection);
    },
    [onChange, trackSelection],
  );

  const editorRef = useRef<HTMLDivElement>(null);
  const cmInstance = useRef<CodeMirror.Editor | null>(null);

  const currentValueRef = useUpdatingRef(value);
  const currentPendingValueRef = useRef(value);
  const setValueTimeoutRef = useRef<null | ReturnType<typeof setTimeout>>(null);

  const hintRef = useUpdatingRef(
    useMemo(() => {
      return createSelectionHint({nameBase, attributesMap, functions});
    }, [nameBase, attributesMap, functions]),
  );

  useLayoutEffect(() => {
    if (editorRef.current && !cmInstance.current) {
      cmInstance.current = CodeMirror(editorRef.current, {
        value,
        mode: 'assetSelection',
        lineNumbers: false,
        lineWrapping: false,
        scrollbarStyle: 'native',
        autoCloseBrackets: true,
        lint: {
          getAnnotations: linter,
          async: false,
        },
        placeholder,
        extraKeys: {
          'Ctrl-Space': 'autocomplete',
          Tab: (cm: Editor) => {
            cm.replaceSelection('  ', 'end');
          },
        },
      });

      cmInstance.current.setSize('100%', 20);

      // Enforce single line by preventing newlines
      cmInstance.current.on('beforeChange', (_instance: Editor, change) => {
        if (change.text.some((line) => line.includes('\n'))) {
          change.cancel();
        }
      });

      cmInstance.current.on('change', (instance: Editor, change) => {
        const newValue = instance.getValue().replace(/\s+/g, ' ');
        currentPendingValueRef.current = newValue;
        if (setValueTimeoutRef.current) {
          clearTimeout(setValueTimeoutRef.current);
        }
        setValueTimeoutRef.current = setTimeout(() => {
          onSelectionChange(newValue);
        }, 2000);

        if (change.origin === 'complete' && change.text[0]?.endsWith('()')) {
          // Set cursor inside the right parenthesis
          const cursor = instance.getCursor();
          instance.setCursor({...cursor, ch: cursor.ch - 1});
        }
      });

      cmInstance.current.on('inputRead', (instance: Editor) => {
        showHint(instance, hintRef.current);
      });

      cmInstance.current.on('focus', (instance: Editor) => {
        showHint(instance, hintRef.current);
      });

      cmInstance.current.on('cursorActivity', (instance: Editor) => {
        applyStaticSyntaxHighlighting(instance);
        showHint(instance, hintRef.current);
      });

      cmInstance.current.on('blur', () => {
        if (currentPendingValueRef.current !== currentValueRef.current) {
          onSelectionChange(currentPendingValueRef.current);
        }
      });

      requestAnimationFrame(() => {
        if (!cmInstance.current) {
          return;
        }

        applyStaticSyntaxHighlighting(cmInstance.current);
      });
    }

    return () => {
      const cm = cmInstance.current;
      if (cm) {
        // Clean up the instance...
        cm.closeHint();
        cm.getWrapperElement()?.parentNode?.removeChild(cm.getWrapperElement());
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update CodeMirror when value prop changes
  useLayoutEffect(() => {
    const noNewLineValue = value.replace('\n', ' ');
    if (cmInstance.current && cmInstance.current.getValue() !== noNewLineValue) {
      const instance = cmInstance.current;
      const cursor = instance.getCursor();
      instance.setValue(noNewLineValue);
      instance.setCursor(cursor);
      showHint(instance, hintRef.current);
    }
  }, [hintRef, value]);

  return (
    <>
      <GlobalHintStyles />
      <InputDiv
        style={{
          display: 'grid',
          gridTemplateColumns: 'auto minmax(0, 1fr) auto',
          alignItems: 'center',
        }}
      >
        <Icon name="op_selector" />
        <div ref={editorRef} />
      </InputDiv>
    </>
  );
};

export const iconStyle = (img: string) => css`
  &:before {
    content: ' ';
    width: 14px;
    mask-size: contain;
    mask-repeat: no-repeat;
    mask-position: center;
    mask-image: url(${img});
    background: ${Colors.accentPrimary()};
    display: inline-block;
  }
`;

export const InputDiv = styled.div`
  ${SelectionAutoCompleteInputCSS}
`;

// Z-index: 21 to beat out Dialog's z-index: 20
const GlobalHintStyles = createGlobalStyle`
  .CodeMirror-hints {
    z-index: 21;
    background: ${Colors.popoverBackground()};
    border: none;
    border-radius: 4px;
    padding: 8px 4px;
    .CodeMirror-hint {
      border-radius: 4px;
      font-size: 14px;
      padding: 6px 8px 6px 12px;
      color: ${Colors.textDefault()};
      &:hover,
      &.CodeMirror-hint-active {
        background-color: ${Colors.backgroundBlue()};
        color: ${Colors.textDefault()};
      }
    }
  }
`;

function showHint(instance: Editor, hint: HintFunction) {
  if (document.body.querySelector('.CodeMirror-hints')) {
    // Hints already visible
    return;
  }
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      if (instance.getWrapperElement().contains(document.activeElement)) {
        instance.showHint({
          hint,
          completeSingle: false,
          moveOnOverlap: true,
          updateOnCursorActivity: true,
          completeOnSingleClick: true,
        });
      }
    });
  });
}
