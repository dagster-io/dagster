import {Colors, Icon, Popover} from '@dagster-io/ui-components';
import useResizeObserver from '@react-hook/resize-observer';
import CodeMirror, {Editor} from 'codemirror';
import {Linter} from 'codemirror/addon/lint/lint';
import debounce from 'lodash/debounce';
import React, {KeyboardEvent, useCallback, useLayoutEffect, useMemo, useRef, useState} from 'react';
import styled, {css} from 'styled-components';

import {Suggestion} from './SelectionAutoCompleteVisitor';
import {SelectionInputAutoCompleteResults} from './SelectionInputAutoCompleteResults';
import {
  SelectionAutoCompleteInputCSS,
  applyStaticSyntaxHighlighting,
} from './SelectionInputHighlighter';
import {useTrackEvent} from '../app/analytics';
import {useDangerousRenderEffect} from '../hooks/useDangerousRenderEffect';

import 'codemirror/addon/edit/closebrackets';
import 'codemirror/lib/codemirror.css';
import 'codemirror/addon/lint/lint.css';
import 'codemirror/addon/display/placeholder';

type SelectionAutoCompleteInputProps = {
  id: string; // Used for logging
  placeholder: string;
  linter: Linter<any>;
  value: string;
  onChange: (value: string) => void;
  useAutoComplete: (
    selection: string,
    cursor: number,
  ) => {
    autoCompleteResults: {
      list: Suggestion[];
      from: number;
      to: number;
    };
    loading: boolean;
  };
};

export const SelectionAutoCompleteInput = ({
  id,
  value,
  placeholder,
  onChange,
  linter,
  useAutoComplete,
}: SelectionAutoCompleteInputProps) => {
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

  const currentPendingValueRef = useRef(value);
  const setValueTimeoutRef = useRef<null | ReturnType<typeof setTimeout>>(null);

  const [showResults, setShowResults] = useState({current: false});
  const [cursorPosition, setCursorPosition] = useState<number>(0);
  const [innerValue, setInnerValue] = useState(value);

  const {autoCompleteResults, loading} = useAutoComplete(innerValue, cursorPosition);

  const hintContainerRef = useRef<HTMLDivElement | null>(null);

  const focusRef = useRef(false);

  const [selectedIndexRef, setSelectedIndex] = useState({current: 0});

  const scrollToSelectionRef = useRef(false);

  useDangerousRenderEffect(() => {
    // Rather then using a useEffect + setState (extra render), we just set the current value directly
    selectedIndexRef.current = 0;
    if (!autoCompleteResults?.list.length && !loading) {
      showResults.current = false;
    }
    scrollToSelectionRef.current = true;
  }, [autoCompleteResults, loading]);

  const scheduleUpdateValue = useCallback(() => {
    if (setValueTimeoutRef.current) {
      clearTimeout(setValueTimeoutRef.current);
    }
    setValueTimeoutRef.current = setTimeout(() => {
      onSelectionChange(currentPendingValueRef.current);
    }, 2000);
  }, [onSelectionChange]);

  useLayoutEffect(() => {
    if (editorRef.current && !cmInstance.current) {
      cmInstance.current = CodeMirror(editorRef.current, {
        value,
        mode: 'assetSelection',
        lineNumbers: false,
        lineWrapping: false, // Initially false; enable during focus
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
        if (change.text.length !== 1 || change.text[0]?.includes('\n')) {
          change.cancel();
        }
      });

      cmInstance.current.on('change', (instance: Editor) => {
        const newValue = instance.getValue().replace(/\s+/g, ' ');
        currentPendingValueRef.current = newValue;
        setInnerValue(newValue);
        scheduleUpdateValue();
        setShowResults({current: true});
        adjustHeight();
        setCursorPosition(instance.getCursor().ch);
      });

      cmInstance.current.on('inputRead', (instance: Editor) => {
        setShowResults({current: true});
        setCursorPosition(instance.getCursor().ch);
      });

      cmInstance.current.on('focus', (instance: Editor) => {
        focusRef.current = true;
        instance.setOption('lineWrapping', true);
        adjustHeight();
        setShowResults({current: true});
      });

      cmInstance.current.on('cursorActivity', (instance: Editor) => {
        applyStaticSyntaxHighlighting(instance);
        setCursorPosition(instance.getCursor().ch);
        setShowResults({current: true});
      });

      cmInstance.current.on('blur', (instance: Editor, ev: FocusEvent) => {
        focusRef.current = false;
        instance.setOption('lineWrapping', false);
        instance.setSize('100%', '20px');
        const current = document.activeElement;
        const hintsVisible = !!hintContainerRef.current?.querySelector('.CodeMirror-hints');
        if (
          editorRef.current?.contains(current) ||
          hintContainerRef.current?.contains(current) ||
          hintsVisible
        ) {
          ev.preventDefault();
          return;
        }
      });

      requestAnimationFrame(() => {
        if (!cmInstance.current) {
          return;
        }

        applyStaticSyntaxHighlighting(cmInstance.current);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const adjustHeight = useCallback(() => {
    const lines = cmInstance.current?.getWrapperElement().querySelector('.CodeMirror-lines');
    if (!lines || !cmInstance.current || !focusRef.current) {
      return;
    }
    requestAnimationFrame(() => {
      const linesHeight = lines?.clientHeight;
      if (linesHeight && focusRef.current) {
        cmInstance.current?.setSize('100%', `${linesHeight}px`);
      }
    });
  }, []);

  // Update CodeMirror when value prop changes
  useLayoutEffect(() => {
    const noNewLineValue = value.replace('\n', ' ');
    if (cmInstance.current && cmInstance.current.getValue() !== noNewLineValue) {
      const instance = cmInstance.current;
      const cursor = instance.getCursor();
      instance.setValue(noNewLineValue);
      instance.setCursor(cursor);
      setCursorPosition(cursor.ch);
      setShowResults({current: true});
      requestAnimationFrame(() => {
        // Reset selected index on value change
        setSelectedIndex({current: 0});
      });
    }
  }, [value]);

  const inputRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  useResizeObserver(inputRef, () => {
    if (inputRef.current) {
      setWidth(inputRef.current.clientWidth);
    }
  });

  const selectedItem = autoCompleteResults?.list[selectedIndexRef.current];

  const onSelect = useCallback(
    (suggestion: Suggestion) => {
      if (autoCompleteResults && suggestion && cmInstance.current) {
        const editor = cmInstance.current;
        editor.replaceRange(
          suggestion.text,
          {line: 0, ch: autoCompleteResults.from},
          {line: 0, ch: autoCompleteResults.to},
          'complete',
        );
        editor.focus();
        const cursor = editor.getCursor();
        let offset = 0;
        if (suggestion.text.endsWith('()')) {
          offset = -1;
        }
        editor.setCursor({
          ...cursor,
          ch: autoCompleteResults.from + suggestion.text.length + offset,
        });
      }
    },
    [autoCompleteResults],
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      if (!showResults.current) {
        return;
      }
      scheduleUpdateValue();
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        scrollToSelectionRef.current = true;
      }
      if (e.key === 'ArrowDown' && !e.shiftKey && !e.ctrlKey) {
        e.preventDefault();
        setSelectedIndex((prev) => ({
          current: (prev.current + 1) % (autoCompleteResults?.list.length ?? 0),
        }));
      } else if (e.key === 'ArrowUp' && !e.shiftKey && !e.ctrlKey) {
        e.preventDefault();
        setSelectedIndex((prev) => ({
          current:
            prev.current - 1 < 0 ? (autoCompleteResults?.list.length ?? 1) - 1 : prev.current - 1,
        }));
      } else if (e.key === 'Tab') {
        e.preventDefault();
        if (selectedItem) {
          onSelect(selectedItem);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setShowResults({current: false});
      }
    },
    [showResults, scheduleUpdateValue, autoCompleteResults, selectedItem, onSelect],
  );

  /**
   * Popover doesn't seem to support canOutsideClickClose, so we have to do this ourselves.
   */
  React.useLayoutEffect(() => {
    const listener = (e: MouseEvent) => {
      if (
        inputRef.current?.contains(e.target as Node) ||
        hintContainerRef.current?.contains(e.target as Node) ||
        !document.contains(e.target as Node)
      ) {
        return;
      }
      setShowResults({current: false});
    };
    document.body.addEventListener('mousedown', listener);
    return () => {
      document.body.removeEventListener('mousedown', listener);
    };
  }, [setShowResults]);

  return (
    <>
      <Popover
        content={
          <div ref={hintContainerRef} onMouseMove={scheduleUpdateValue} onKeyDown={handleKeyDown}>
            <SelectionInputAutoCompleteResults
              results={autoCompleteResults}
              width={width}
              selectedIndex={selectedIndexRef.current}
              scrollToSelection={scrollToSelectionRef}
              onSelect={onSelect}
              scheduleUpdateValue={scheduleUpdateValue}
              setSelectedIndex={setSelectedIndex}
              loading={loading}
            />
          </div>
        }
        placement="bottom-start"
        isOpen={loading || autoCompleteResults?.list.length ? showResults.current : false}
        targetTagName="div"
        canEscapeKeyClose={true}
      >
        <InputDiv
          style={{
            display: 'grid',
            gridTemplateColumns: 'auto minmax(0, 1fr) auto',
            alignItems: 'flex-start',
          }}
          ref={inputRef}
          onKeyDownCapture={handleKeyDown} // Added keyboard event handler
          tabIndex={0} // Make the div focusable to capture keyboard events
          onClick={() => {
            setShowResults({current: true});
          }}
        >
          <Icon name="op_selector" style={{marginTop: 2}} />
          <div ref={editorRef} />
        </InputDiv>
      </Popover>
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
