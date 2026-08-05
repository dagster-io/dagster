import {useVirtualizer} from '@tanstack/react-virtual';
import clsx from 'clsx';
import * as React from 'react';

import {Box} from './Box';
import {Icon} from './Icon';
import {MenuItem} from './Menu';
import {Popover} from './Popover';
import {Spinner} from './Spinner';
import {Container, Inner, Row} from './VirtualizedTable';
import styles from './css/TokenizingField.module.css';

const MAX_SUGGESTIONS = 100;
const MENU_ITEM_HEIGHT = 32;

const defaultRenderSuggestion = (suggestion: Suggestion) => suggestion.text;

export interface SuggestionProvider {
  token?: string;
  values: () => string[];
  suggestionFilter?: (query: string, suggestion: Suggestion) => boolean;
  textOnly?: boolean;
}

export interface Suggestion {
  text: string;
  final: boolean;
}

interface ActiveSuggestionInfo {
  text: string;
  idx: number;
}

export type TokenizingFieldValue = {
  token?: string;
  value: string;
};

interface TokenizingFieldProps {
  values: TokenizingFieldValue[];
  maxValues?: number;
  onChange: (values: TokenizingFieldValue[]) => void;
  onChangeBeforeCommit?: boolean;
  addOnBlur?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;

  placeholder?: string;
  loading?: boolean;
  className?: string;
  small?: boolean;

  fullwidth?: boolean;

  onTextChange?: (text: string) => void;
  suggestionProviders: SuggestionProvider[];
  suggestionRenderer?: (suggestion: Suggestion) => React.ReactNode;
  suggestionProvidersFilter?: (
    suggestionProvider: SuggestionProvider[],
    values: TokenizingFieldValue[],
  ) => SuggestionProvider[];
}

function findProviderByToken(token: string, providers: SuggestionProvider[]) {
  return providers.find((p) => p.token && p.token.toLowerCase() === token.toLowerCase());
}

export const tokenizedValuesFromString = (str: string, providers: SuggestionProvider[]) => {
  if (str === '') {
    return [];
  }
  const tokens = str.split(',');
  return tokenizedValuesFromStringArray(tokens, providers);
};

export const tokenizedValuesFromStringArray = (tokens: string[], providers: SuggestionProvider[]) =>
  tokens.map((token) => tokenizedValueFromString(token, providers));

export const tokenizeString = (str: string): [string, string] => {
  const colonAt = str.indexOf(':');
  if (colonAt === -1) {
    return [str, ''];
  }
  return [str.slice(0, colonAt), str.slice(colonAt + 1)];
};

export function tokenizedValueFromString(
  str: string,
  providers: SuggestionProvider[],
): TokenizingFieldValue {
  const [token, value] = tokenizeString(str);
  if (findProviderByToken(token, providers)) {
    if (token && value) {
      return {token, value};
    }
  }

  return {value: str};
}

export const tokenToString = (v: TokenizingFieldValue) =>
  v.token ? `${v.token}:${v.value}` : v.value;

export const tokensAsStringArray = (value: TokenizingFieldValue[]) =>
  value.filter((v) => v.value !== '').map(tokenToString);

export const stringFromValue = (value: TokenizingFieldValue[]) =>
  tokensAsStringArray(value).join(',');

const isEqual = (a: TokenizingFieldValue, b?: TokenizingFieldValue) =>
  b && a.token === b.token && a.value === b.value;

/** Provides a text field with typeahead autocompletion.
 *  This completion either provides a list of standalone tokens
 *  sourced from the `tokens` param, or a set of key value pairs,
 *  sourced from the `suggestionProviders` param. In the latter case, the
 *  key is one of a known set of "suggestion provider tokens".
 *
 *  Provide one or more SuggestionProviders or a list of tokens
 *  to build the tree of autocompletions.
 *
 *  The input also allows for freeform typing (`value` items with no token value) */
export const TokenizingField = ({
  suggestionProviders,
  suggestionProvidersFilter,
  values: externalValues,
  maxValues,
  onChange,
  onChangeBeforeCommit,
  onFocus,
  onBlur,
  onTextChange,
  placeholder,
  addOnBlur,
  loading,
  className,
  fullwidth,
  suggestionRenderer,
}: TokenizingFieldProps) => {
  const [open, setOpen] = React.useState<boolean>(false);
  const [active, setActive] = React.useState<ActiveSuggestionInfo | null>(null);
  const [typed, setTyped] = React.useState<string>('');
  const [focused, setFocused] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const values = React.useMemo(() => [...externalValues], [externalValues]);
  const typedValue = tokenizedValueFromString(typed, suggestionProviders);
  if (isEqual(typedValue, values[values.length - 1])) {
    values.pop();
  }

  const atMaxValues = maxValues !== undefined && values.length >= maxValues;

  const filteredSuggestionProviders = suggestionProvidersFilter
    ? suggestionProvidersFilter(suggestionProviders, values)
    : suggestionProviders;

  // Build the set of suggestions that should be displayed for the current input value.
  // Note: "typed" is the text that has not yet been submitted, separate from values[].
  const parts = typed.split(':');
  const lastPart = (parts[parts.length - 1] || '').toLowerCase();

  const suggestions = React.useMemo(() => {
    if (atMaxValues) {
      return [];
    }

    let suggestionsArr: Suggestion[] = [];

    const matchesTypedText = (query: string, s: Suggestion) =>
      !query ||
      s.text
        .toLowerCase()
        .split(':')
        .some((c) => c.includes(query));

    const availableSuggestionsForProvider = (provider: SuggestionProvider) => {
      const suggestionNotUsed = (v: string) =>
        !values.some((e) => e.token === provider.token && e.value === v);

      const suggestionFilter = provider.suggestionFilter || matchesTypedText;

      return provider
        .values()
        .filter(suggestionNotUsed)
        .map((v) => ({
          text: provider?.token ? `${provider.token}:${v}` : v,
          final: !provider.textOnly,
        }))
        .filter((s) => suggestionFilter(lastPart, s))
        .slice(0, MAX_SUGGESTIONS); // never show too many suggestions for one provider
    };

    if (parts.length === 1) {
      // Suggest providers (eg: `pipeline:`) so users can discover the search space

      suggestionsArr = filteredSuggestionProviders
        .reduce((accum: Suggestion[], s) => {
          if (s.token) {
            accum.push({text: `${s.token}:`, final: false});
          }
          return accum;
        }, [])
        .filter((s) => matchesTypedText(lastPart, s));

      // Suggest value completions so users can type "airline_" without the "pipeline"
      // prefix and get the correct suggestion.
      for (const p of filteredSuggestionProviders) {
        if (!p.token || typed.length > 0) {
          suggestionsArr.push(...availableSuggestionsForProvider(p));
        }
      }
    }

    if (parts.length === 2) {
      const firstPart = parts[0];
      if (firstPart) {
        // Suggest values from the chosen provider (eg: `pipeline:abc`)
        const provider = findProviderByToken(firstPart, filteredSuggestionProviders);
        suggestionsArr = provider ? availableSuggestionsForProvider(provider) : [];
      }
    }

    // Truncate suggestions to the ones currently matching the typed text,
    // and always sort them in alphabetical order.
    suggestionsArr.sort((a, b) => a.text.localeCompare(b.text));

    return suggestionsArr;
  }, [atMaxValues, filteredSuggestionProviders, lastPart, parts, typed.length, values]);

  const _onTextChange = (text: string) => {
    setTyped(text);
    setActive(null);
    if (onTextChange) {
      onTextChange(text);
    }
  };

  // We need to manage selection in the dropdown by ourselves. To ensure the
  // best behavior we store the active item's index and text (the text allows
  // us to relocate it if it's moved and the index allows us to keep selection
  // at the same location if the previous item is gone.)

  // This hook keeps the active row state in sync with the suggestions, which
  // are derived from the current input value.

  React.useEffect(() => {
    // If suggestions are present, autoselect the first one so the user can press
    // enter to complete their search. (Esc + enter is how you enter your raw text.)
    if (!active && suggestions.length) {
      const item = suggestions[0];
      if (item) {
        setActive({text: item.text, idx: 0});
      }
      return;
    }
    if (!active) {
      return;
    }
    if (suggestions.length === 0) {
      setActive(null);
      return;
    }

    // Relocate the currently active item in the latest suggestions list
    const pos = suggestions.findIndex((a) => a.text === active.text);

    // The new index is the index of the active item, or whatever item
    // is now at it's location if it's gone, bounded to the array.
    let nextIdx = pos !== -1 ? pos : active.idx;
    nextIdx = Math.max(0, Math.min(suggestions.length - 1, nextIdx));
    const nextItem = suggestions[nextIdx];

    if (nextItem && (nextIdx !== active.idx || nextItem.text !== active.text)) {
      setActive({text: nextItem.text, idx: nextIdx});
    }
  }, [active, suggestions]);

  const onConfirmSuggestion = (suggestion: Suggestion) => {
    if (atMaxValues) {
      return;
    }

    if (suggestion.final) {
      // The user has finished a key-value pair
      onConfirmText(suggestion.text);
      _onTextChange('');
      setActive(null);
      setOpen(false);
    } else {
      // The user has finished a key
      _onTextChange(suggestion.text);
    }
  };

  const onConfirmText = (str: string) => {
    if (atMaxValues) {
      return;
    }
    if (str.endsWith(':')) {
      return;
    }
    if (str === '') {
      return;
    }

    _onTextChange('');
    onChange([...values, tokenizedValueFromString(str, filteredSuggestionProviders)]);
  };

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    if (atMaxValues && e.key !== 'Delete' && e.key !== 'Backspace') {
      e.preventDefault();
      e.stopPropagation();
      return;
    }

    // Backspace removes the last tag when the input is empty
    if (e.key === 'Backspace' && typed === '' && values.length > 0) {
      const next = [...values];
      next.pop();
      onChange(next);
      return;
    }

    // Enter and Return confirm the currently selected suggestion or
    // confirm the freeform text you've typed if no suggestions are shown.
    if (e.key === 'Enter' || e.key === 'Return' || e.key === 'Tab') {
      if (active) {
        const picked = suggestions.find((s) => s.text === active.text);
        if (!picked) {
          throw new Error('Selection out of sync with suggestions');
        }
        onConfirmSuggestion(picked);
        e.preventDefault();
        e.stopPropagation();
      } else if (typed.length) {
        onConfirmText(typed);
        e.preventDefault();
        e.stopPropagation();
      }
      return;
    }

    // Typing space confirms your freeform text
    if (e.key === ' ') {
      e.preventDefault();
      onConfirmText(typed);
      return;
    }

    // Escape closes the options. The options re-open if you type another char or click.
    if (e.key === 'Escape') {
      setActive(null);
      setOpen(false);
      return;
    }

    if (!open && e.key !== 'Delete' && e.key !== 'Backspace') {
      setOpen(true);
    }

    // The up/down arrow keys shift selection in the dropdown.
    // Note: The first down arrow press activates the first item.
    const shift = {ArrowDown: 1, ArrowUp: -1}[e.key];
    if (shift && suggestions.length > 0) {
      e.preventDefault();
      let idx = (active ? active.idx : -1) + shift;
      idx = Math.max(0, Math.min(idx, suggestions.length - 1));
      const item = suggestions[idx];
      if (item) {
        setActive({text: item.text, idx});
      }
    }
  };

  const renderSuggestion = suggestionRenderer || defaultRenderSuggestion;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const text = e.currentTarget.value;
    _onTextChange(text);

    if (onChangeBeforeCommit && text !== '' && !text.endsWith(':')) {
      const tokenized = tokenizedValueFromString(text, filteredSuggestionProviders);
      onChange([...values, tokenized]);
    }
  };

  const handleFocus = React.useCallback(() => {
    setFocused(true);
    setOpen(true);
    onFocus?.();
  }, [onFocus]);

  const handleBlur = () => {
    setFocused(false);
    if (addOnBlur) {
      onConfirmText(typed);
    }
    setOpen(false);
    onBlur?.();
  };

  const onClearActive = React.useCallback(() => setActive(null), []);

  return (
    <Popover
      isOpen={open && suggestions.length > 0 && !atMaxValues}
      position="bottom-left"
      content={
        suggestions.length > 0 ? (
          <SuggestionList
            suggestions={suggestions}
            activeIdx={active?.idx ?? -1}
            onConfirmSuggestion={onConfirmSuggestion}
            onClearActive={onClearActive}
            renderSuggestion={renderSuggestion}
          />
        ) : (
          <div />
        )
      }
    >
      <div
        className={clsx(
          styles.styledTagInput,
          fullwidth && styles.fullWidth,
          className,
          focused && styles.active,
        )}
        onClick={() => inputRef.current?.focus()}
      >
        <div className={styles.tagInputValues}>
          {values.map((v, idx) => {
            const text = v.token ? `${v.token}:${v.value}` : v.value;
            return (
              <span key={`${text}-${idx}`} className={clsx(styles.tag, styles.tagDefault)}>
                <span className={styles.tagText}>{text}</span>
                <button
                  className={styles.tagRemove}
                  onClick={(e) => {
                    e.stopPropagation();
                    const next = [...values];
                    next.splice(idx, 1);
                    onChange(next);
                  }}
                  tabIndex={-1}
                  type="button"
                  aria-label="Remove"
                >
                  <Icon name="close" size={12} />
                </button>
              </span>
            );
          })}
          <input
            ref={inputRef}
            className={clsx(styles.input, values.length === 0 && styles.inputFirst)}
            value={typed}
            onChange={handleInputChange}
            onKeyDown={onKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={values.length === 0 ? placeholder || 'Search\u2026' : undefined}
          />
        </div>
        {loading && open ? (
          <Box style={{alignSelf: 'center'}} margin={{right: 4}}>
            <Spinner purpose="body-text" />
          </Box>
        ) : null}
      </div>
    </Popover>
  );
};

interface SuggestionListProps {
  suggestions: Suggestion[];
  activeIdx: number;
  onConfirmSuggestion: (suggestion: Suggestion) => void;
  onClearActive: () => void;
  renderSuggestion: (suggestion: Suggestion) => React.ReactNode;
}

const SuggestionList = ({
  suggestions,
  activeIdx,
  onConfirmSuggestion,
  onClearActive,
  renderSuggestion,
}: SuggestionListProps) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: suggestions.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => MENU_ITEM_HEIGHT,
    overscan: 10,
  });

  React.useEffect(() => {
    if (activeIdx >= 0) {
      rowVirtualizer.scrollToIndex(activeIdx, {align: 'auto'});
    }
  }, [rowVirtualizer, activeIdx]);

  return (
    <Container ref={parentRef} className={styles.suggestionList}>
      <Inner totalHeight={rowVirtualizer.getTotalSize()}>
        {rowVirtualizer.getVirtualItems().map(({index, key, size, start}) => {
          const suggestion = suggestions[index];
          if (!suggestion) {
            return null;
          }
          return (
            <Row key={key} height={size} start={start}>
              <MenuItem
                text={renderSuggestion(suggestion)}
                active={activeIdx === index}
                onMouseDown={(e: React.MouseEvent<HTMLButtonElement>) => {
                  e.preventDefault();
                  if (e.button !== 0 || e.metaKey || e.ctrlKey) {
                    return;
                  }
                  e.stopPropagation();
                  onConfirmSuggestion(suggestion);
                  onClearActive();
                }}
              />
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};
