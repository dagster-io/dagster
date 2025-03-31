import {Box, Colors, Icon, Popover, UnstyledButton} from '@dagster-io/ui-components';
import useResizeObserver from '@react-hook/resize-observer';
import CodeMirror, {Editor, EditorChange} from 'codemirror';
import debounce from 'lodash/debounce';
import React, {
  KeyboardEvent,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import styled from 'styled-components';

import {SyntaxError} from './CustomErrorListener';
import {SelectionAutoCompleteProvider} from './SelectionAutoCompleteProvider';
import {SelectionInputAutoCompleteResults} from './SelectionInputAutoCompleteResults';
import {SelectionAutoCompleteInputCSS} from './SelectionInputHighlighter';
import {useSelectionInputLintingAndHighlighting} from './useSelectionInputLintingAndHighlighting';
import {useTrackEvent} from '../app/analytics';
import {upgradeSyntax} from '../asset-selection/syntaxUpgrader';
import {useDangerousRenderEffect} from '../hooks/useDangerousRenderEffect';
import {usePrevious} from '../hooks/usePrevious';
import {useUpdatingRef} from '../hooks/useUpdatingRef';

import 'codemirror/addon/edit/closebrackets';
import 'codemirror/lib/codemirror.css';
import 'codemirror/addon/lint/lint.css';
import 'codemirror/addon/lint/lint';
import 'codemirror/addon/display/placeholder';

type SelectionAutoCompleteInputProps = {
  id: string; // Used for logging
  placeholder: string;
  linter: (content: string) => SyntaxError[];
  value: string;
  useAutoComplete: SelectionAutoCompleteProvider['useAutoComplete'];
  saveOnBlur?: boolean;
  onErrorStateChange?: (errors: SyntaxError[]) => void;
  onChange: (value: string) => void;
  wildcardAttributeName: string;
};

const emptyArray: SyntaxError[] = [];
export const SelectionAutoCompleteInput = ({
  id,
  value,
  placeholder,
  onChange,
  linter,
  useAutoComplete,
  saveOnBlur = false,
  onErrorStateChange,
  wildcardAttributeName,
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
      let nextValue = selection;
      if (wildcardAttributeName) {
        nextValue = upgradeSyntax(selection, wildcardAttributeName);
      }
      onChange(nextValue);
      trackSelection(nextValue);
    },
    [onChange, trackSelection, wildcardAttributeName],
  );

  const editorRef = useRef<HTMLDivElement>(null);
  const cmInstance = useRef<CodeMirror.Editor | null>(null);

  const [selectedIndexRef, setSelectedIndex] = useState({current: -1});
  const [showResults, _setShowResults] = useState({current: false});
  const showResultsRef = useUpdatingRef(showResults.current);
  const setShowResults = useCallback(
    (nextShowResults: {current: boolean}) => {
      if (showResultsRef.current !== nextShowResults.current) {
        selectedIndexRef.current = -1;
      }
      _setShowResults(nextShowResults);
    },
    [_setShowResults, selectedIndexRef, showResultsRef],
  );
  const [cursorPosition, setCursorPosition] = useState<number>(0);
  const [innerValue, setInnerValue] = useState(value);
  const cursorPositionRef = useUpdatingRef(cursorPosition);

  const {autoCompleteResults, loading} = useAutoComplete({
    line: innerValue,
    cursorIndex: cursorPosition,
  });

  const hintContainerRef = useRef<HTMLDivElement | null>(null);

  const focusRef = useRef(false);

  // Memoize the stringified results to avoid resetting the selected index down below
  const resultsJson = useMemo(() => {
    return JSON.stringify(autoCompleteResults?.list.map((l) => l.text));
  }, [autoCompleteResults]);

  const prevJson = usePrevious(resultsJson);
  const prevAutoCompleteResults = usePrevious(autoCompleteResults);

  // Handle selection reset
  useDangerousRenderEffect(() => {
    if (prevAutoCompleteResults?.from !== autoCompleteResults?.from || prevJson !== resultsJson) {
      selectedIndexRef.current = -1;
    }
  }, [resultsJson, autoCompleteResults, prevAutoCompleteResults, prevJson, selectedIndexRef]);

  // Handle hiding results
  useDangerousRenderEffect(() => {
    if (!autoCompleteResults.list.length && !loading) {
      showResults.current = false;
    }
  }, [autoCompleteResults, loading]);

  useLayoutEffect(() => {
    if (editorRef.current && !cmInstance.current) {
      cmInstance.current = CodeMirror(editorRef.current, {
        value,
        mode: 'assetSelection',
        lineNumbers: false,
        lineWrapping: false, // Initially false; enable during focus
        scrollbarStyle: 'native',
        autoCloseBrackets: true,
        placeholder,
        extraKeys: {
          'Ctrl-Space': 'autocomplete',
          Tab: (cm: Editor) => {
            cm.replaceSelection('  ', 'end');
          },
        },
      });

      cmInstance.current.setSize('100%', 20);
      setCurrentHeight(20);

      // Enforce single line by preventing newlines
      cmInstance.current.on('beforeChange', (_instance: Editor, change) => {
        if (
          change.text.length !== 1 ||
          change.text[0]?.includes('\n') ||
          change.text[0]?.includes('  ')
        ) {
          change.cancel();
        }
      });

      cmInstance.current.on('change', (instance: Editor, changeObj: EditorChange) => {
        const newValue = instance.getValue().replace(/\s+/g, ' ');
        const cursor = instance.getCursor();
        if (instance.getValue() !== newValue) {
          const difference = newValue.length - instance.getValue().length;
          // In this case they added a space, we removed it,
          // so we need to move the cursor back one character
          instance.setValue(newValue);
          instance.setCursor({...cursor, ch: cursor.ch - difference});
        }
        setInnerValue(newValue);
        if (changeObj.origin !== 'setValue') {
          // If we're programmatically setting the value, we don't want to display the dropdown
          // automatically.
          setShowResults({current: true});
        }
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
        const nextCursorPosition = instance.getCursor().ch;
        if (cursorPositionRef.current !== nextCursorPosition) {
          // If the cursor has moved then update the cursor position
          // and show the auto-complete results.
          setCursorPosition(nextCursorPosition);
          setShowResults({current: true});
        }
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const errorTooltip = useSelectionInputLintingAndHighlighting({
    cmInstance,
    linter,
  });

  const [currentHeight, setCurrentHeight] = useState(20);

  const adjustHeight = useCallback(() => {
    const lines = cmInstance.current?.getWrapperElement().querySelector('.CodeMirror-lines');
    if (!lines || !cmInstance.current || !focusRef.current) {
      return;
    }
    requestAnimationFrame(() => {
      const linesHeight = lines?.clientHeight;
      if (linesHeight && focusRef.current) {
        cmInstance.current?.setSize('100%', `${linesHeight}px`);
        setCurrentHeight(linesHeight);
      }
    });
  }, []);

  // Update CodeMirror when value prop changes
  useLayoutEffect(() => {
    const noNewLineValue = value.replace(/\n/g, ' ');
    const currentValue = cmInstance.current?.getValue();
    if (cmInstance.current && currentValue !== noNewLineValue) {
      const instance = cmInstance.current;
      const cursor = instance.getCursor();
      setCursorPosition(cursor.ch);
      requestAnimationFrame(() => {
        instance.setValue(noNewLineValue);
        instance.setCursor(cursor);
        // Reset selected index on value change
        setSelectedIndex({current: -1});
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
    (suggestion: {text: string}) => {
      if (autoCompleteResults && suggestion && cmInstance.current) {
        const editor = cmInstance.current;
        editor.replaceRange(
          suggestion.text,
          {line: 0, ch: autoCompleteResults.from},
          {line: 0, ch: autoCompleteResults.to},
          'complete',
        );
        editor.focus();
        let offset = 0;
        if (suggestion.text.endsWith('()')) {
          offset = -1;
        }
        editor.setCursor({
          line: 0,
          ch: autoCompleteResults.from + suggestion.text.length + offset,
        });
      }
    },
    [autoCompleteResults],
  );

  const innerValueRef = useUpdatingRef(innerValue);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      if (e.key === 'Enter') {
        if (selectedIndexRef.current !== -1 && selectedItem) {
          onSelect(selectedItem);
        } else {
          e.stopPropagation();
          e.preventDefault();
          onSelectionChange(innerValueRef.current);
          setShowResults({current: false});
        }
      } else if (!showResults.current) {
        return;
      } else if (e.key === 'ArrowDown' && !e.shiftKey && !e.ctrlKey) {
        e.preventDefault();
        e.stopPropagation();
        setSelectedIndex((prev) => ({
          current: (prev.current + 1) % (autoCompleteResults?.list.length ?? 0),
        }));
      } else if (e.key === 'ArrowUp' && !e.shiftKey && !e.ctrlKey) {
        e.preventDefault();
        e.stopPropagation();
        setSelectedIndex((prev) => ({
          current:
            prev.current - 1 < 0 ? (autoCompleteResults?.list.length ?? 1) - 1 : prev.current - 1,
        }));
      } else if (e.key === 'Tab') {
        e.preventDefault();
        e.stopPropagation();
        if (selectedItem) {
          onSelect(selectedItem);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        setShowResults({current: false});
      }
    },
    [
      showResults,
      selectedIndexRef,
      selectedItem,
      onSelect,
      onSelectionChange,
      innerValueRef,
      setShowResults,
      autoCompleteResults?.list.length,
    ],
  );

  /**
   * Popover doesn't seem to support canOutsideClickClose, so we have to do this ourselves.
   */
  useLayoutEffect(() => {
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

  const isEmpty = innerValue === '';
  useLayoutEffect(() => {
    requestAnimationFrame(() => {
      adjustHeight();
    });
  }, [adjustHeight, isEmpty]);

  const onBlur = useCallback(
    (ev: React.FocusEvent<HTMLDivElement>) => {
      const current = ev.relatedTarget;
      const hintsVisible = !!hintContainerRef.current?.querySelector('.CodeMirror-hints');
      if (saveOnBlur) {
        onSelectionChange(innerValueRef.current);
      }
      if (
        inputRef.current?.contains(current) ||
        editorRef.current?.contains(current) ||
        hintContainerRef.current?.contains(current) ||
        hintsVisible
      ) {
        ev.preventDefault();
        return;
      }
      focusRef.current = false;
      cmInstance.current?.setOption('lineWrapping', false);
      cmInstance.current?.setSize('100%', '20px');
      setCurrentHeight(20);
    },
    [saveOnBlur, onSelectionChange, innerValueRef],
  );

  useResizeObserver(inputRef, adjustHeight);

  const errors = useMemo(() => {
    const linterErrors = linter(value);
    if (linterErrors.length > 0) {
      return linterErrors;
    }
    // Keep the reference the same to avoid re-rendering
    return emptyArray;
  }, [linter, value]);

  useEffect(() => {
    onErrorStateChange?.(errors);
  }, [onErrorStateChange, errors]);

  return (
    <div onBlur={onBlur} style={{width: '100%'}}>
      <Popover
        content={
          <div ref={hintContainerRef} onKeyDown={handleKeyDown}>
            <SelectionInputAutoCompleteResults
              results={autoCompleteResults}
              width={width}
              selectedIndex={selectedIndexRef.current}
              onSelect={onSelect}
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
          $isCommitted={innerValue === value}
          $hasErrors={errors.length > 0}
          style={{
            display: 'grid',
            gridTemplateColumns: 'auto minmax(0, 1fr) auto',
            contain: 'layout paint style',
          }}
          ref={inputRef}
          onKeyDownCapture={handleKeyDown} // Added keyboard event handler
          tabIndex={0} // Make the div focusable to capture keyboard events
          onClick={() => {
            setShowResults({current: true});
          }}
        >
          <div style={{alignSelf: currentHeight > 20 ? 'flex-start' : 'center'}}>
            <Icon name="search" style={{marginTop: 2}} />
          </div>
          <div ref={editorRef} />
          <Box
            flex={{direction: 'row', alignItems: 'center', gap: 4}}
            style={{alignSelf: currentHeight > 20 ? 'flex-end' : 'center'}}
          >
            {innerValue !== '' && (
              <UnstyledButton
                onClick={() => {
                  cmInstance.current?.setValue('');
                  onSelectionChange('');
                  setShowResults({current: false});
                }}
              >
                <Icon name="close" />
              </UnstyledButton>
            )}
          </Box>
        </InputDiv>
      </Popover>
      {errorTooltip}
    </div>
  );
};

export const InputDiv = styled.div<{$isCommitted: boolean; $hasErrors: boolean}>`
  ${SelectionAutoCompleteInputCSS}
  ${({$isCommitted}) =>
    $isCommitted
      ? ''
      : `
      background: ${Colors.backgroundLight()}; 
      `}
  ${({$hasErrors}) =>
    $hasErrors
      ? `
      border: 1px solid ${Colors.accentRed()};
      `
      : ''}
`;
