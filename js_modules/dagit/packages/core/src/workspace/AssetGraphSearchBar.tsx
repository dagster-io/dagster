import {Colors, Icon, Popover, Tag} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import Fuse from 'fuse.js';
import * as React from 'react';
import styled from 'styled-components/macro';

import {iconForType, SearchResults} from '../search/SearchResults';
import {SearchResult, SearchResultType} from '../search/types';
import {useRepoSearch} from '../search/useRepoSearch';
import {Box} from '../ui/Box';
import {Spinner} from '../ui/Spinner';
import {FontFamily} from '../ui/styles';

const SEARCH_TYPES = {
  [SearchResultType.Asset]: false,
  [SearchResultType.Pipeline]: true,
  [SearchResultType.Schedule]: true,
  [SearchResultType.Sensor]: true,
};

type State = {
  queryString: string;
  searching: boolean;
  results: Fuse.FuseResult<SearchResult>[];
  highlight: number;
  loaded: boolean;
};
type Action =
  | {type: 'show-dialog'}
  | {type: 'hide-dialog'}
  | {type: 'highlight'; highlight: number}
  | {type: 'change-query'; queryString: string}
  | {type: 'complete-search'; results: Fuse.FuseResult<SearchResult>[]};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'show-dialog':
      return {...state, shown: true, loaded: true};
    case 'hide-dialog':
      return {...state, shown: false, queryString: ''};
    case 'highlight':
      return {...state, highlight: action.highlight};
    case 'change-query':
      return {...state, queryString: action.queryString, searching: true, highlight: 0};
    case 'complete-search':
      return {...state, results: action.results, searching: false};
    default:
      return state;
  }
};

const initialState: State = {
  queryString: '',
  searching: false,
  results: [],
  highlight: 0,
  loaded: false,
};

export const AssetGraphSearchBar = ({
  selected,
  onSelectItem,
  onClear,
}: {
  selected?: SearchResult;
  onSelectItem: (item: SearchResult) => void;
  onClear: () => void;
}) => {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {queryString, results, highlight, loaded} = state;
  const {loading, performSearch} = useRepoSearch();
  const onChange = React.useCallback((e) => {
    dispatch({type: 'change-query', queryString: e.target.value});
  }, []);
  React.useEffect(() => {
    const results = performSearch(queryString, loaded).filter((x) => SEARCH_TYPES[x.item.type]);
    dispatch({type: 'complete-search', results});
  }, [queryString, performSearch, loaded]);
  const highlightedResult = results[highlight] || null;
  const onClickResult = (result: Fuse.FuseResult<SearchResult>) => {
    dispatch({type: 'hide-dialog'});
    onSelectItem(result.item);
  };
  const onKeyDown = (e: React.KeyboardEvent) => {
    const {key} = e;
    if (key === 'Escape') {
      dispatch({type: 'hide-dialog'});
      return;
    }

    if (!results.length) {
      return;
    }

    const lastResult = results.length - 1;

    switch (key) {
      case 'ArrowUp':
        e.preventDefault();
        dispatch({
          type: 'highlight',
          highlight: highlight === 0 ? lastResult : highlight - 1,
        });
        break;
      case 'ArrowDown':
        e.preventDefault();
        dispatch({
          type: 'highlight',
          highlight: highlight === lastResult ? 0 : highlight + 1,
        });
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedResult) {
          dispatch({type: 'hide-dialog'});
          onSelectItem(highlightedResult.item);
        }
    }
  };

  return (
    <Box
      flex={{alignItems: 'center', direction: 'column'}}
      padding={24}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
      }}
    >
      <div style={{width: 750}}>
        <Popover
          minimal
          fill={true}
          isOpen={!!results.length}
          usePortal={false}
          content={
            <SearchResults
              highlight={highlight}
              queryString={queryString}
              results={results}
              onClickResult={onClickResult}
              style={{width: 750}}
            />
          }
        >
          <SearchBox hasQueryString={!!queryString.length}>
            {selected ? (
              <Tag
                icon={<Icon icon={iconForType(selected.type, true)} iconSize={12} />}
                rightIcon={
                  <Icon
                    icon={IconNames.CROSS}
                    iconSize={12}
                    style={{cursor: 'pointer'}}
                    onClick={() => onClear()}
                  />
                }
              >
                {selected.label}
              </Tag>
            ) : (
              <>
                <Icon icon="search" iconSize={18} color={Colors.LIGHT_GRAY3} />
                {loading ? <Spinner purpose="body-text" /> : null}
                <SearchInput
                  autoFocus
                  spellCheck={false}
                  onChange={onChange}
                  onKeyDown={onKeyDown}
                  placeholder="Search jobs, schedules, sensors…"
                  type="text"
                  value={queryString}
                />
              </>
            )}
          </SearchBox>
        </Popover>
      </div>
    </Box>
  );
};

interface SearchBoxProps {
  readonly hasQueryString: boolean;
}

const SearchBox = styled.div<SearchBoxProps>`
  align-items: center;
  border: 1px solid ${Colors.LIGHT_GRAY2};
  border-radius: 5px;
  display: flex;
  padding: 8px;
  ${({hasQueryString}) =>
    hasQueryString
      ? `
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  `
      : ''}
`;

const SearchInput = styled.input`
  border: none;
  color: ${Colors.GRAY1};
  font-family: ${FontFamily.default};
  font-size: 18px;
  margin-left: 8px;
  outline: none;
  width: 100%;

  &::placeholder {
    color: ${Colors.GRAY5};
  }
`;
