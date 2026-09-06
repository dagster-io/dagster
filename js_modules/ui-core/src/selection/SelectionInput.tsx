import {Box, Icon, MiddleTruncate, Popover, UnstyledButton} from '@dagster-io/ui-components';
import useResizeObserver from '@react-hook/resize-observer';
import clsx from 'clsx';
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

import {SyntaxError} from './CustomErrorListener';
import {SelectionAutoCompleteProvider, SuggestionJSXBase} from './SelectionAutoCompleteProvider';
import {
  ResultItem,
  SelectionInputAutoCompleteResults,
  isSelectableResult,
} from './SelectionInputAutoCompleteResults';
import inputStyles from './css/SelectionInput.module.css';
import {MAX_RECENT_SUGGESTIONS, useRecentSelections} from './useRecentSelections';
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
  onChange?: (value: string) => void;
  // Omitting onChange will make the input read only
  onSubmit?: (value: string) => void;
  className?: string;

  // Providing a key enables the "recent searches" section shown when the input is empty.
  recentSearchesKey?: string;

  wildcardAttributeName: string;
};

const emptyArray: SyntaxError[] = [];

const DIVIDER: ResultItem = {type: 'divider'};

const toRecentItem = (text: string): ResultItem => ({
  type: 'recent',
  text,
  jsx: <SuggestionJSXBase icon="history" label={<MiddleTruncate text={text} />} />,
});

export const getNextSelectableIndex = (list: ResultItem[], current: number, delta: number) => {
  if (!list.length) {
    return -1;
  }
  let next: number;
  if (current < 0) {
    // With nothing selected, the first step lands on the first row going down and the
    // last row going up.
    next = delta > 0 ? -1 : 0;
  } else {
    next = current;
  }
  for (let i = 0; i < list.length; i++) {
    next = (next + delta + list.length) % list.length;
    const item = list[next];
    if (item && isSelectableResult(item)) {
      return next;
    }
  }
  return -1;
};
export const SelectionAutoCompleteInput = ({
  id,
  value,
  placeholder,
  onChange,
  onSubmit,
  linter,
  useAutoComplete,
  saveOnBlur = false,
  onErrorStateChange,
  wildcardAttributeName,
  recentSearchesKey,
  className,
}: SelectionAutoCompleteInputProps) => {
  const onSubmitRef = useUpdatingRef(onSubmit);
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
      onChange?.(nextValue);
      trackSelection(nextValue);
      return nextValue;
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

  const {recentSelections, addRecentSelection} = useRecentSelections(recentSearchesKey);

  const displayList: ResultItem[] = useMemo(() => {
    const suggestions = autoCompleteResults?.list ?? [];
    if (innerValue.trim() !== '' || !recentSelections.length) {
      return suggestions;
    }
    return [
      ...recentSelections.slice(0, MAX_RECENT_SUGGESTIONS).map(toRecentItem),
      DIVIDER,
      ...suggestions,
    ];
  }, [autoCompleteResults, innerValue, recentSelections]);

  // Memoized so the memoized results list doesn't re-render on every keystroke.
  const results = useMemo(
    () => ({
      from: autoCompleteResults?.from ?? 0,
      to: autoCompleteResults?.to ?? 0,
      list: displayList,
    }),
    [autoCompleteResults, displayList],
  );

  // Memoize the stringified results to avoid resetting the selected index down below
  const resultsJson = useMemo(() => {
    return JSON.stringify(displayList.map((l) => ('text' in l ? l.text : l.type)));
  }, [displayList]);

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
    if (!displayList.length && !loading) {
      showResults.current = false;
    }
  }, [displayList, loading]);

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
        readOnly: disabled ? 'nocursor' : false,
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
        if (change.text[0] && /\s+/.test(change.text[0])) {
          change.text[0] = change.text[0].replace(/\s+/g, ' ');
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

  // Suppress lint errors while the autocomplete dropdown is open — the
  // in-progress expression often produces cascading parser errors that span
  // the current token and everything after it, which is noisy while the user
  // is still picking a suggestion.
  const suppressErrors = !!(loading || displayList.length) && showResults.current && !!onChange;

  const errorTooltip = useSelectionInputLintingAndHighlighting({
    cmInstance,
    linter,
    suppressErrors,
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

  const selectedItem = displayList[selectedIndexRef.current];

  const fillWithRecent = useCallback((text: string) => {
    const editor = cmInstance.current;
    if (editor) {
      editor.setValue(text);
      editor.focus();
      editor.setCursor({line: 0, ch: text.length});
    }
  }, []);

  const onSelect = useCallback(
    (suggestion: ResultItem) => {
      if (!isSelectableResult(suggestion)) {
        return;
      }
      if ('type' in suggestion) {
        fillWithRecent(suggestion.text);
        onSelectionChange(suggestion.text);
        onSubmitRef.current?.(suggestion.text);
        addRecentSelection(suggestion.text);
        // Must come last: focusing and moving the cursor both re-open the dropdown.
        setShowResults({current: false});
        return;
      }
      if (autoCompleteResults && suggestion && cmInstance.current) {
        const editor = cmInstance.current;
        const insertText = suggestion.trailingSpace ? suggestion.text + ' ' : suggestion.text;
        editor.replaceRange(
          insertText,
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
          ch: autoCompleteResults.from + insertText.length + offset,
        });
      }
    },
    [
      autoCompleteResults,
      fillWithRecent,
      onSelectionChange,
      onSubmitRef,
      addRecentSelection,
      setShowResults,
    ],
  );

  const innerValueRef = useUpdatingRef(innerValue);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      if (e.key === 'Enter') {
        if (selectedIndexRef.current !== -1 && selectedItem) {
          e.preventDefault();
          e.stopPropagation();
          onSelect(selectedItem);
        } else {
          e.stopPropagation();
          e.preventDefault();
          // The committed value is syntax-upgraded, so replaying a recent search from
          // history runs exactly what this search ran.
          const committed = onSelectionChange(innerValueRef.current);
          onSubmitRef.current?.(committed);
          // A query that doesn't parse is about to be retyped; don't keep it.
          if (!linter(committed).length) {
            addRecentSelection(committed);
          }
          setShowResults({current: false});
        }
      } else if (!showResults.current) {
        return;
      } else if (e.key === 'ArrowDown' && !e.shiftKey && !e.ctrlKey) {
        e.preventDefault();
        e.stopPropagation();
        setSelectedIndex((prev) => ({
          current: getNextSelectableIndex(displayList, prev.current, 1),
        }));
      } else if (e.key === 'ArrowUp' && !e.shiftKey && !e.ctrlKey) {
        e.preventDefault();
        e.stopPropagation();
        setSelectedIndex((prev) => ({
          current: getNextSelectableIndex(displayList, prev.current, -1),
        }));
      } else if (e.key === 'Tab') {
        e.preventDefault();
        e.stopPropagation();
        if (selectedItem && 'type' in selectedItem && selectedItem.type === 'recent') {
          // Tab fills in without running, as it does for suggestions. Enter runs it.
          fillWithRecent(selectedItem.text);
        } else if (selectedItem) {
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
      onSubmitRef,
      innerValueRef,
      setShowResults,
      addRecentSelection,
      fillWithRecent,
      linter,
      displayList,
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

  const disabled = !onChange;

  const errors = useMemo(() => {
    if (disabled) {
      return emptyArray;
    }
    const linterErrors = linter(value);
    if (linterErrors.length > 0) {
      return linterErrors;
    }
    // Keep the reference the same to avoid re-rendering
    return emptyArray;
  }, [linter, value, disabled]);

  useEffect(() => {
    onErrorStateChange?.(errors);
  }, [onErrorStateChange, errors]);

  return (
    <div onBlur={onBlur} style={{width: '100%'}}>
      <Popover
        content={
          <div ref={hintContainerRef} onKeyDown={handleKeyDown}>
            <SelectionInputAutoCompleteResults
              results={results}
              width={width}
              selectedIndex={selectedIndexRef.current}
              onSelect={onSelect}
              loading={loading}
            />
          </div>
        }
        placement="bottom-start"
        isOpen={(loading || displayList.length ? showResults.current : false) && !disabled}
        targetTagName="div"
        canEscapeKeyClose={true}
      >
        <div
          className={clsx(
            inputStyles.inputDiv,
            className,
            innerValue !== value && inputStyles.uncommitted,
            errors.length > 0 && inputStyles.hasErrors,
            disabled && inputStyles.disabled,
          )}
          style={{
            display: 'grid',
            gridTemplateColumns: 'auto minmax(0, 1fr) auto',
            contain: 'layout paint style',
          }}
          ref={inputRef}
          onKeyDownCapture={handleKeyDown} // Added keyboard event handler
          tabIndex={-1} // Make the div focusable to capture keyboard events
          onClick={() => {
            setShowResults({current: true});
            cmInstance.current?.focus();
          }}
        >
          <div style={{alignSelf: currentHeight > 20 ? 'flex-start' : 'center', width: 18}}>
            <Icon name="search" style={{marginTop: 2}} />
          </div>
          <div ref={editorRef} />
          <Box
            flex={{direction: 'row', alignItems: 'center', gap: 4}}
            style={{alignSelf: currentHeight > 20 ? 'flex-end' : 'center'}}
          >
            {innerValue !== '' && !disabled && (
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
        </div>
      </Popover>
      {errorTooltip}
    </div>
  );
};
