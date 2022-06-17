// eslint-disable-next-line no-restricted-imports
import {TagInput} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {Colors} from './Colors';
import {MenuItem, Menu} from './Menu';
import {Popover} from './Popover';
import {Spinner} from './Spinner';

const MAX_SUGGESTIONS = 100;

export interface SuggestionProvider {
  token: string;
  values: () => string[];
}

interface Suggestion {
  text: string;
  final: boolean;
}

interface ActiveSuggestionInfo {
  text: string;
  idx: number;
}

export interface TokenizingFieldValue {
  token?: string;
  value: string;
}

interface TokenizingFieldProps {
  values: TokenizingFieldValue[];
  maxValues?: number;
  onChange: (values: TokenizingFieldValue[]) => void;
  onChangeBeforeCommit?: boolean;
  onFocus?: () => void;

  placeholder?: string;
  loading?: boolean;
  className?: string;
  small?: boolean;

  fullwidth?: boolean;

  tokens?: string[];
  tokensFilter?: (query: string, token: string) => boolean;

  suggestionProviders?: SuggestionProvider[];
  suggestionRenderer?: (suggestion: Suggestion) => React.ReactNode;
  suggestionProvidersFilter?: (
    suggestionProvider: SuggestionProvider[],
    values: TokenizingFieldValue[],
  ) => SuggestionProvider[];
}

function findProviderByToken(token: string, providers: SuggestionProvider[]) {
  return providers.find((p) => p.token.toLowerCase() === token.toLowerCase());
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

export const tokensAsStringArray = (value: TokenizingFieldValue[]) =>
  value.filter((v) => v.value !== '').map((v) => (v.token ? `${v.token}:${v.value}` : v.value));

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
export const TokenizingField: React.FC<TokenizingFieldProps> = ({
  suggestionProviders: rawSuggestionProviders,
  suggestionProvidersFilter,
  values: externalValues,
  maxValues,
  onChange,
  onChangeBeforeCommit,
  onFocus,
  placeholder,
  loading,
  className,
  tokens,
  tokensFilter,
  fullwidth,
  suggestionRenderer,
}) => {
  const suggestionProviders = rawSuggestionProviders || [];
  const [open, setOpen] = React.useState<boolean>(false);
  const [active, setActive] = React.useState<ActiveSuggestionInfo | null>(null);
  const [typed, setTyped] = React.useState<string>('');

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

    const suggestionMatchesTypedText = (s: Suggestion) =>
      !lastPart ||
      s.text
        .toLowerCase()
        .split(':')
        .some((c) => c.includes(lastPart));

    const availableSuggestionsForProvider = (provider: SuggestionProvider) => {
      const suggestionNotUsed = (v: string) =>
        !values.some((e) => e.token === provider.token && e.value === v);

      return provider
        .values()
        .filter(suggestionNotUsed)
        .map((v) => ({text: `${provider.token}:${v}`, final: true}))
        .filter(suggestionMatchesTypedText)
        .slice(0, MAX_SUGGESTIONS); // never show too many suggestions for one provider
    };

    if (parts.length === 1) {
      // Suggest providers (eg: `pipeline:`) so users can discover the search space
      const actualTokenFilter = tokensFilter
        ? tokensFilter
        : (query: string, token: string) => token.toLowerCase().includes(query.toLowerCase());

      const filteredTokens = tokens
        ? tokens
            .filter(
              (token) =>
                !values.some((e) => e.value === token) && actualTokenFilter(lastPart, token),
            )
            .map((token) => ({text: token, final: true}))
        : [];
      suggestionsArr = filteredSuggestionProviders
        .map((s) => ({text: `${s.token}:`, final: false}))
        .filter(suggestionMatchesTypedText)
        .concat(filteredTokens);

      // Suggest value completions so users can type "airline_" without the "pipeline"
      // prefix and get the correct suggestion.
      if (typed.length > 0) {
        for (const p of filteredSuggestionProviders) {
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
  }, [
    atMaxValues,
    filteredSuggestionProviders,
    lastPart,
    parts,
    typed.length,
    values,
    tokens,
    tokensFilter,
  ]);

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
      setTyped('');
      setActive(null);
      setOpen(false);
    } else {
      // The user has finished a key
      setTyped(suggestion.text);
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

    setTyped('');
    onChange([...values, tokenizedValueFromString(str, filteredSuggestionProviders)]);
  };

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    if (atMaxValues && e.key !== 'Delete' && e.key !== 'Backspace') {
      e.preventDefault();
      e.stopPropagation();
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

  const menuRef = React.createRef<HTMLDivElement>();
  React.useEffect(() => {
    if (menuRef.current && active) {
      const el = menuRef.current.querySelector(`[data-idx='${active.idx}']`);
      if (el && el instanceof HTMLElement && 'scrollIntoView' in el) {
        el.scrollIntoView({block: 'nearest'});
      }
    }
  }, [menuRef, active]);

  const renderSuggestion = suggestionRenderer || ((suggestion) => suggestion.text);

  return (
    <Popover
      isOpen={open && suggestions.length > 0 && !atMaxValues}
      position="bottom-left"
      content={
        suggestions.length > 0 ? (
          <div style={{maxHeight: 235, overflowY: 'scroll'}} ref={menuRef}>
            <StyledMenu>
              {suggestions.map((suggestion, idx) => (
                <MenuItem
                  data-idx={idx}
                  key={suggestion.text}
                  text={renderSuggestion(suggestion)}
                  shouldDismissPopover={false}
                  active={active?.idx === idx}
                  onMouseDown={(e: React.MouseEvent<any>) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onConfirmSuggestion(suggestion);
                    setActive(null);
                  }}
                />
              ))}
            </StyledMenu>
          </div>
        ) : (
          <div />
        )
      }
    >
      <StyledTagInput
        className={className}
        values={values.map((v) => (v.token ? `${v.token}:${v.value}` : v.value))}
        inputValue={typed}
        onRemove={(_, idx) => {
          const next = [...values];
          next.splice(idx, 1);
          onChange(next);
        }}
        onInputChange={(e) => {
          setTyped(e.currentTarget.value);

          if (onChangeBeforeCommit) {
            const tokenized = tokenizedValueFromString(
              e.currentTarget.value,
              filteredSuggestionProviders,
            );
            onChange([...values, tokenized]);
          }
        }}
        inputProps={{
          onFocus: () => {
            setOpen(true);
            onFocus && onFocus();
          },
          onBlur: () => setOpen(false),
        }}
        $maxWidth={fullwidth ? '100%' : undefined}
        onAdd={() => false}
        onKeyDown={onKeyDown}
        tagProps={{minimal: true}}
        placeholder={placeholder || 'Filter…'}
        rightElement={
          loading && open ? (
            <Box style={{alignSelf: 'center'}} margin={{right: 4}}>
              <Spinner purpose="body-text" />
            </Box>
          ) : undefined
        }
      />
      <StyledTagInput />
    </Popover>
  );
};

export const StyledTagInput = styled(TagInput)<{$maxWidth?: any}>`
  border: none;
  border-radius: 8px;
  box-shadow: ${Colors.Gray300} inset 0px 0px 0px 1px, ${Colors.KeylineGray} inset 2px 2px 1.5px;
  min-width: 400px;
  max-width: ${(p) => (p.$maxWidth ? p.$maxWidth : '600px')};
  transition: box-shadow 150ms;

  &.bp3-active {
    box-shadow: ${Colors.Gray300} inset 0px 0px 0px 1px, ${Colors.KeylineGray} inset 2px 2px 1.5px,
      rgba(58, 151, 212, 0.6) 0 0 0 3px;
  }

  input {
    font-size: 14px;
    font-weight: 400;
    padding-left: 4px;
    padding-bottom: 2px;
    padding-top: 2px;
  }

  && .bp3-tag-input-values:first-child .bp3-input-ghost:first-child {
    padding-left: 8px;
  }

  && .bp3-tag-input-values {
    margin-right: 4px;
    margin-top: 4px;
  }

  && .bp3-tag-input-values > * {
    margin-bottom: 4px;
  }

  .bp3-tag {
    border-radius: 6px;
    display: inline-flex;
    flex-direction: row;
    font-size: 12px;
    line-height: 16px;
    align-items: center;
    max-width: 400px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    padding: 4px 8px;
    user-select: none;
  }

  .bp3-tag.bp3-minimal:not([class*='bp3-intent-']) {
    background-color: ${Colors.Gray100};
    color: ${Colors.Gray900};
  }

  .bp3-tag.bp3-minimal.bp3-intent-success {
    background-color: ${Colors.Green50};
    color: ${Colors.Green700};
  }

  .bp3-tag.bp3-minimal.bp3-intent-warning {
    background-color: ${Colors.Yellow50};
    color: ${Colors.Yellow700};
  }

  .bp3-tag.bp3-minimal.bp3-intent-danger {
    background-color: ${Colors.Red50};
    color: ${Colors.Red700};
  }
`;

const StyledMenu = styled(Menu)`
  width: 400px;
`;
