import {Menu, MenuItem, TagInput} from '@blueprintjs/core';
import isEqual from 'lodash/isEqual';
import React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {ColorsWIP} from './Colors';
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

  suggestionProviders: SuggestionProvider[];
  suggestionProvidersFilter?: (
    suggestionProvider: SuggestionProvider[],
    values: TokenizingFieldValue[],
  ) => SuggestionProvider[];
}

function findProviderByToken(token: string, providers: SuggestionProvider[]) {
  return providers.find((p) => p.token.toLowerCase() === token.toLowerCase());
}

export function tokenizedValuesFromString(str: string, providers: SuggestionProvider[]) {
  if (str === '') {
    return [];
  }
  const tokens = str.split(',');
  return tokens.map((token) => tokenizedValueFromString(token, providers));
}

export function tokenizedValueFromString(
  str: string,
  providers: SuggestionProvider[],
): TokenizingFieldValue {
  const parts = str.split(':');
  const token = parts[0];
  if (findProviderByToken(token, providers)) {
    if (parts.length === 2) {
      return {token, value: parts[1]};
    }
    // Jobs can be `pipeline:mode` tuples, so join the "value" tokens back together.
    if (token === 'job') {
      return {token, value: parts.slice(1).join(':')};
    }
  }
  return {value: str};
}

export function stringFromValue(value: TokenizingFieldValue[]) {
  return value
    .filter((v) => v.value !== '')
    .map((v) => (v.token ? `${v.token}:${v.value}` : v.value))
    .join(',');
}

/** Provides a text field with typeahead autocompletion for key value pairs,
where the key is one of a known set of "suggestion provider tokens". Provide
one or more SuggestionProviders to build the tree of autocompletions. The
input also allows for freeform typing (`value` items with no token value) */
export const TokenizingField: React.FC<TokenizingFieldProps> = ({
  suggestionProviders,
  suggestionProvidersFilter,
  values: externalValues,
  maxValues,
  onChange,
  onChangeBeforeCommit,
  onFocus,
  placeholder,
  loading,
  className,
}) => {
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
  const lastPart = parts[parts.length - 1].toLowerCase();
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
      suggestionsArr = filteredSuggestionProviders
        .map((s) => ({text: `${s.token}:`, final: false}))
        .filter(suggestionMatchesTypedText);

      // Suggest value completions so users can type "airline_" without the "pipeline"
      // prefix and get the correct suggestion.
      if (typed.length > 0) {
        for (const p of filteredSuggestionProviders) {
          suggestionsArr.push(...availableSuggestionsForProvider(p));
        }
      }
    }

    if (parts.length === 2) {
      // Suggest values from the chosen provider (eg: `pipeline:abc`)
      const provider = findProviderByToken(parts[0], filteredSuggestionProviders);
      suggestionsArr = provider ? availableSuggestionsForProvider(provider) : [];
    }

    // Truncate suggestions to the ones currently matching the typed text,
    // and always sort them in alphabetical order.
    suggestionsArr.sort((a, b) => a.text.localeCompare(b.text));

    return suggestionsArr;
  }, [atMaxValues, filteredSuggestionProviders, lastPart, parts, typed.length, values]);

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
      setActive({text: suggestions[0].text, idx: 0});
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
    const nextText = suggestions[nextIdx] && suggestions[nextIdx].text;

    if (nextIdx !== active.idx || nextText !== active.text) {
      setActive({text: nextText, idx: nextIdx});
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
      setActive({text: suggestions[idx].text, idx});
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

  return (
    <Popover
      isOpen={open && suggestions.length > 0 && !atMaxValues}
      position="bottom-left"
      content={
        suggestions.length > 0 ? (
          <div style={{maxHeight: 235, overflowY: 'scroll'}} ref={menuRef}>
            <StyledMenu>
              {suggestions.map((suggestion, idx) => (
                <StyledMenuItem
                  data-idx={idx}
                  key={suggestion.text}
                  text={suggestion.text}
                  shouldDismissPopover={false}
                  active={active ? active.idx === idx : false}
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
    </Popover>
  );
};

const StyledTagInput = styled(TagInput)`
  border: none;
  border-radius: 8px;
  box-shadow: ${ColorsWIP.Gray300} inset 0px 0px 0px 1px;
  min-width: 400px;
  max-width: 600px;
  transition: box-shadow 150ms;

  &.bp3-active {
    box-shadow: ${ColorsWIP.Gray300} inset 0px 0px 0px 1px, rgba(58, 151, 212, 0.6) 0 0 0 3px;
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
    background-color: ${ColorsWIP.Gray100};
    color: ${ColorsWIP.Gray900};
  }

  .bp3-tag.bp3-minimal.bp3-intent-success {
    background-color: ${ColorsWIP.Green50};
    color: ${ColorsWIP.Green700};
  }

  .bp3-tag.bp3-minimal.bp3-intent-warning {
    background-color: ${ColorsWIP.Yellow50};
    color: ${ColorsWIP.Yellow700};
  }

  .bp3-tag.bp3-minimal.bp3-intent-danger {
    background-color: ${ColorsWIP.Red50};
    color: ${ColorsWIP.Red700};
  }
`;

const StyledMenu = styled(Menu)`
  width: 400px;
`;

const StyledMenuItem = styled(MenuItem)`
  font-size: 13px;
  line-height: 15px;
`;
