import {
  Colors,
  Popover,
  TextInput,
  SuggestionProvider,
  useSuggestionsForString,
  Icon,
} from '@dagster-io/ui';
import Fuse from 'fuse.js';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ClearButton} from '../ui/ClearButton';

interface Props {
  value: string;
  onChange: (value: string) => void;
  suggestionProviders: SuggestionProvider[];
}

type Action =
  | {type: 'show-popover'}
  | {type: 'hide-popover'}
  | {type: 'highlight'; highlight: number}
  | {type: 'change-query'}
  | {type: 'select-suggestion'};

type State = {
  shown: boolean;
  highlight: number;
};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'show-popover':
      return {...state, shown: true};
    case 'hide-popover':
      return {...state, shown: false};
    case 'highlight':
      return {...state, highlight: action.highlight};
    case 'change-query':
      return {...state, shown: true, highlight: 0};
    case 'select-suggestion':
      return {...state, highlight: 0};
    default:
      return state;
  }
};

const initialState: State = {
  shown: false,
  highlight: 0,
};

const fuseOptions = {
  threshold: 0.3,
};

export const LogsFilterInput: React.FC<Props> = (props) => {
  const {value, onChange, suggestionProviders} = props;

  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {shown, highlight} = state;
  const inputRef = React.useRef<HTMLInputElement>(null);

  const {empty, perProvider} = React.useMemo(() => {
    const perProvider = suggestionProviders.reduce((accum, provider) => {
      const values = provider.values();
      return {...accum, [provider.token]: {fuse: new Fuse(values, fuseOptions), all: values}};
    }, {} as {[token: string]: {fuse: Fuse<string>; all: string[]}});
    const providerKeys = suggestionProviders.map((provider) => provider.token);
    return {
      empty: new Fuse(providerKeys, fuseOptions),
      perProvider,
    };
  }, [suggestionProviders]);

  const buildSuggestions = React.useCallback(
    (queryString: string): string[] => {
      if (!queryString) {
        return Object.keys(perProvider);
      }

      const [token, value] = queryString.split(':');
      if (token in perProvider) {
        const {fuse, all} = perProvider[token];
        const results = value
          ? fuse.search(value).map((result) => `${token}:${result.item}`)
          : all.map((value) => `${token}:${value}`);

        // If the querystring is an exact match, don't suggest anything.
        return results.map((result) => result.toLowerCase()).includes(queryString) ? [] : results;
      }

      return empty.search(queryString).map((result) => result.item);
    },
    [empty, perProvider],
  );

  const {suggestions, onSelectSuggestion} = useSuggestionsForString(buildSuggestions, value);

  const numResults = suggestions.length;
  const highlightedResult = suggestions[highlight] || null;

  const onInputChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      dispatch({type: 'change-query'});
      onChange(e.target.value);
    },
    [onChange],
  );

  const onSelect = React.useCallback(
    (suggestion: string) => {
      dispatch({type: 'select-suggestion'});
      onChange(onSelectSuggestion(suggestion));
    },
    [onChange, onSelectSuggestion],
  );

  const onClear = React.useCallback(() => {
    dispatch({type: 'change-query'});
    onChange('');
    inputRef.current?.focus();
  }, [onChange]);

  const onKeyDown = (e: React.KeyboardEvent) => {
    const {key} = e;
    if (key === 'Escape') {
      dispatch({type: 'hide-popover'});
      return;
    }

    if (!numResults) {
      return;
    }

    const lastResult = numResults - 1;

    switch (key) {
      case 'ArrowUp':
        e.preventDefault();
        dispatch({type: 'highlight', highlight: highlight === 0 ? lastResult : highlight - 1});
        break;
      case 'ArrowDown':
        e.preventDefault();
        dispatch({type: 'highlight', highlight: highlight === lastResult ? 0 : highlight + 1});
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedResult) {
          onSelect(highlightedResult);
        }
    }
  };
  return (
    <Popover
      isOpen={shown && suggestions.length > 0}
      position="bottom-left"
      content={
        <Results>
          {suggestions.map((suggestion, ii) => (
            <ResultItem
              key={suggestion}
              suggestion={suggestion}
              isHighlight={highlight === ii}
              onSelect={onSelect}
            />
          ))}
        </Results>
      }
    >
      <FilterInput
        placeholder="Filter…"
        spellCheck={false}
        autoCorrect="off"
        value={value}
        ref={inputRef}
        onChange={onInputChange}
        onFocus={() => dispatch({type: 'show-popover'})}
        onBlur={() => dispatch({type: 'hide-popover'})}
        onKeyDown={onKeyDown}
        rightElement={
          <ClearButton onClick={onClear}>
            <Icon name="cancel" />
          </ClearButton>
        }
      />
    </Popover>
  );
};

const ResultItem: React.FC<{
  suggestion: string;
  isHighlight: boolean;
  onSelect: (suggestion: string) => void;
}> = (props) => {
  const {suggestion, isHighlight, onSelect} = props;
  const element = React.useRef<HTMLLIElement>(null);

  React.useEffect(() => {
    if (element.current && isHighlight) {
      element.current.scrollIntoView({block: 'nearest'});
    }
  }, [isHighlight]);

  return (
    <Item
      ref={element}
      isHighlight={isHighlight}
      onMouseDown={(e: React.MouseEvent<any>) => {
        e.preventDefault();
        onSelect(suggestion);
      }}
    >
      {suggestion}
    </Item>
  );
};

const FilterInput = styled(TextInput)`
  width: 300px;
`;

const Results = styled.ul`
  list-style: none;
  margin: 0;
  max-height: 200px;
  max-width: 800px;
  min-width: 300px;
  overflow-y: auto;
  padding: 4px 0;
`;

interface HighlightableTextProps {
  readonly isHighlight: boolean;
}

const Item = styled.li<HighlightableTextProps>`
  align-items: center;
  background-color: ${({isHighlight}) => (isHighlight ? Colors.Blue500 : Colors.White)};
  color: ${({isHighlight}) => (isHighlight ? Colors.White : 'default')};
  cursor: pointer;
  display: flex;
  flex-direction: row;
  font-size: 12px;
  list-style: none;
  margin: 0;
  padding: 4px 8px;
  white-space: nowrap;
  text-overflow: ellipsis;

  &:hover {
    background-color: ${({isHighlight}) => (isHighlight ? Colors.Blue500 : Colors.Gray100)};
  }
`;
