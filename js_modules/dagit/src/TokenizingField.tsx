import React from "react";
import { TagInput, Popover, Menu, MenuItem } from "@blueprintjs/core";
import styled from "styled-components";

export interface SuggestionProvider {
  token: string;
  values: () => string[];
}

interface Suggestion {
  text: string;
  completion: string;
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
  maxValues: number | undefined;
  onChange: (values: TokenizingFieldValue[]) => void;
  suggestionProviders: SuggestionProvider[];
}

function findProviderByToken(token: string, providers: SuggestionProvider[]) {
  return providers.find(p => p.token.toLowerCase() === token.toLowerCase());
}

export function tokenizedValuesFromString(
  str: string,
  providers: SuggestionProvider[]
) {
  const tokens = str.split(",");
  return tokens.map(token => tokenizedValueFromString(token, providers));
}

export function tokenizedValueFromString(
  str: string,
  providers: SuggestionProvider[]
) {
  const parts = str.split(":");
  if (parts.length === 2 && findProviderByToken(parts[0], providers)) {
    return { token: parts[0], value: parts[1] };
  }
  return { value: str };
}

export function stringFromValue(value: TokenizingFieldValue[]) {
  return value
    .filter(v => v.value !== "")
    .map(v => (v.token ? `${v.token}:${v.value}` : v.value))
    .join(",");
}

/** Provides a text field with typeahead autocompletion for key value pairs,
where the key is one of a known set of "suggestion provider tokens". Provide
one or more SuggestionProviders to build the tree of autocompletions. The
input also allows for freeform typing (`value` items with no token value) */
export const TokenizingField: React.FunctionComponent<TokenizingFieldProps> = ({
  suggestionProviders,
  values,
  maxValues,
  onChange
}) => {
  const [open, setOpen] = React.useState<boolean>(false);
  const [active, setActive] = React.useState<ActiveSuggestionInfo | null>(null);
  const [inputValue, setInputValue] = React.useState<string>("");
  const atMaxValues =
    maxValues === undefined || values.filter(v => v.token).length >= maxValues;

  // Build the set of suggestions that should be displayed for the current input value.
  // Note: inputValue is the text that has not yet been submitted, separate from values[].
  const parts = inputValue.split(":");
  let suggestions: Suggestion[] = [];

  if (parts.length === 1) {
    // Suggest providers (eg: `pipeline:`)
    suggestions = suggestionProviders.map(s => ({
      text: `${s.token}:`,
      completion: `${s.token}:`,
      final: false
    }));
  }
  if (parts.length === 2) {
    // Suggest values from the chosen provider (eg: `pipeline:abc`)
    const provider = findProviderByToken(parts[0], suggestionProviders);
    suggestions = provider
      ? provider
          .values()
          .filter(
            v => !values.some(e => e.token === provider.token && e.value === v)
          )
          .map(v => ({
            text: v,
            completion: `${provider.token}:${v}`,
            final: true
          }))
      : [];
  }

  // Truncate suggestions to the ones currently matching the typed text,
  // and always sort them in alphabetical order.
  suggestions = suggestions
    .filter(s => !inputValue || s.completion.startsWith(inputValue))
    .sort((a, b) => a.text.localeCompare(b.text));

  // We need to manage selection in the dropdown by ourselves. To ensure the
  // best behavior we store the active item's index and text (the text allows)
  // us to relocate it if it's moved and the index allows us to keep selection
  // at the same location if the previous item is gone.)

  // This hook keeps the active row state in sync with the suggestions, which
  // are derived from the current input value.

  React.useEffect(() => {
    if (!active) return;

    if (suggestions.length === 0) {
      setActive(null);
      return;
    }

    // Relocate the currently active item in the latest suggestions list
    const pos = suggestions.findIndex(a => a.text === active.text);

    // The new index is the index of the active item, or whatever item
    // is now at it's location if it's gone, bounded to the array.
    let nextIdx = pos !== -1 ? pos : active.idx;
    nextIdx = Math.max(0, Math.min(suggestions.length - 1, nextIdx));
    let nextText = suggestions[nextIdx] && suggestions[nextIdx].text;

    if (nextIdx !== active.idx || nextText !== active.text) {
      setActive({ text: nextText, idx: nextIdx });
    }
  }, [active, suggestions]);

  const onConfirmSuggestion = (suggestion: Suggestion) => {
    if (atMaxValues) return;

    if (suggestion.final) {
      // The user has finished a key-value pair
      onConfirmText(suggestion.completion);
      setInputValue("");
      setActive(null);
      setOpen(false);
    } else {
      // The user has finished a key
      setInputValue(suggestion.completion);
    }
  };

  const onConfirmText = (str: string) => {
    if (atMaxValues) return;
    if (str.endsWith(":")) return;
    if (str === "") return;

    onChange([...values, tokenizedValueFromString(str, suggestionProviders)]);
    setInputValue("");
  };

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    if (atMaxValues && e.key !== "Delete" && e.key !== "Backspace") {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    // Enter and Return confirm the currently selected suggestion or
    // confirm the freeform text you've typed if no suggestions are shown.
    if (e.key === "Enter" || e.key === "Return" || e.key === "Tab") {
      if (active) {
        const picked = suggestions.find(s => s.text === active.text);
        if (!picked) throw new Error("Selection out of sync with suggestions");
        onConfirmSuggestion(picked);
        e.preventDefault();
        e.stopPropagation();
      } else if (inputValue.length) {
        onConfirmText(inputValue);
        e.preventDefault();
        e.stopPropagation();
      }
      return;
    }

    // Typing space confirms your freeform text
    if (e.key === " ") {
      e.preventDefault();
      onConfirmText(inputValue);
      return;
    }

    // Escape closes the options. The options re-open if you type another char or click.
    if (e.key === "Escape") {
      setOpen(false);
      return;
    }

    if (!open && (e.key !== "Delete" && e.key !== "Backspace")) {
      setOpen(true);
    }

    // The up/down arrow keys shift selection in the dropdown.
    // Note: The first down arrow press activates the first item.
    const shift = { ArrowDown: 1, ArrowUp: -1 }[e.key];
    if (shift && suggestions.length > 0) {
      e.preventDefault();
      let idx = (active ? active.idx : -1) + shift;
      idx = Math.max(0, Math.min(idx, suggestions.length - 1));
      setActive({ text: suggestions[idx].text, idx });
    }
  };

  return (
    <Popover
      minimal={true}
      isOpen={open && suggestions.length > 0 && !atMaxValues}
      position={"bottom"}
      content={
        suggestions.length > 0 ? (
          <StyledMenu>
            {suggestions.map((suggestion, idx) => (
              <StyledMenuItem
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
        ) : (
          <div />
        )
      }
    >
      <StyledTagInput
        values={values.map(v => (v.token ? `${v.token}:${v.value}` : v.value))}
        inputValue={inputValue}
        onRemove={(_, idx) => {
          const next = [...values];
          next.splice(idx, 1);
          onChange(next);
        }}
        onInputChange={e => setInputValue(e.currentTarget.value)}
        inputProps={{
          onFocus: () => setOpen(true),
          onBlur: () => setOpen(false)
        }}
        onAdd={() => false}
        onKeyDown={onKeyDown}
        tagProps={{ minimal: true }}
        placeholder="Filter..."
      />
    </Popover>
  );
};

const StyledTagInput = styled(TagInput)`
  width: 400px;
  input {
    font-size: 12px;
  }
`;

const StyledMenu = styled(Menu)`
  width: 400px;
`;

const StyledMenuItem = styled(MenuItem)`
  font-size: 13px;
  line-height: 15px;
`;
