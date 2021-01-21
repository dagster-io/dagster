import {Colors, Icon, Overlay} from '@blueprintjs/core';
import Fuse from 'fuse.js';
import * as React from 'react';
import styled from 'styled-components';

import {SearchResults} from 'src/search/SearchResults';
import {SearchResult} from 'src/search/types';
import {useRepoSearch} from 'src/search/useRepoSearch';
import {Group} from 'src/ui/Group';
import {FontFamily} from 'src/ui/styles';

type State = {
  shown: boolean;
  queryString: string;
  searching: boolean;
  results: Fuse.FuseResult<SearchResult>[];
  highlight: number;
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
      return {...state, shown: true};
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
  shown: false,
  queryString: '',
  searching: false,
  results: [],
  highlight: 0,
};

const {useCallback, useEffect, useReducer} = React;

export const SearchDialog = () => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const {shown, queryString, results, highlight} = state;

  const numResults = results.length;

  const performSearch = useRepoSearch();

  const openSearch = useCallback(() => dispatch({type: 'show-dialog'}), []);
  const onChange = useCallback((e) => {
    dispatch({type: 'change-query', queryString: e.target.value});
  }, []);

  useEffect(() => {
    const results = performSearch(queryString);
    dispatch({type: 'complete-search', results});
  }, [queryString, performSearch]);

  const onKeyDown = useCallback(
    (e) => {
      const {key} = e;
      if (key === 'Escape') {
        dispatch({type: 'hide-dialog'});
        return;
      }

      if (!numResults) {
        return;
      }

      switch (key) {
        case 'ArrowUp':
          e.preventDefault();
          dispatch({
            type: 'highlight',
            highlight: highlight === 0 ? numResults - 1 : highlight - 1,
          });
          break;
        case 'ArrowDown':
          e.preventDefault();
          dispatch({
            type: 'highlight',
            highlight: highlight === numResults - 1 ? 0 : highlight + 1,
          });
          break;
        case 'Return':
          e.preventDefault();
          console.log('Go to href!');
      }
    },
    [dispatch, highlight, numResults],
  );

  return (
    <>
      <SearchTrigger onClick={openSearch}>
        <Group direction="row" alignItems="center" spacing={8}>
          <Icon icon="search" iconSize={11} color={Colors.GRAY3} style={{display: 'block'}} />
          <div>Search…</div>
        </Group>
      </SearchTrigger>
      <Overlay
        backdropProps={{style: {backgroundColor: 'rgba(0, 0, 0, .15)'}}}
        canEscapeKeyClose
        canOutsideClickClose
        isOpen={shown}
        transitionDuration={100}
      >
        <Container>
          <SearchBox hasQueryString={!!queryString.length}>
            <Icon icon="search" iconSize={18} color={Colors.LIGHT_GRAY3} />
            <SearchInput
              autoFocus
              onChange={onChange}
              onKeyDown={onKeyDown}
              placeholder="Search pipelines, schedules, etc…"
              type="text"
              value={queryString}
            />
          </SearchBox>
          <SearchResults highlight={highlight} queryString={queryString} results={results} />
        </Container>
      </Overlay>
    </>
  );
};

const SearchTrigger = styled.button`
  background-color: ${Colors.WHITE};
  border: 1px solid ${Colors.LIGHT_GRAY1};
  border-radius: 3px;
  color: ${Colors.GRAY1};
  font-size: 14px;
  font-weight: 400;
  -webkit-font-smoothing: antialiased;
  cursor: pointer;
  padding: 4px 10px;
  width: 100%;
`;

const Container = styled.div`
  background-color: ${Colors.WHITE};
  border-radius: 4px;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1);
  max-height: 60vh;
  left: calc(50% - 200px);
  overflow: hidden;
  width: 400px;
  top: 20vh;
`;

interface SearchBoxProps {
  readonly hasQueryString: boolean;
}

const SearchBox = styled.div<SearchBoxProps>`
  align-items: center;
  border-bottom: ${({hasQueryString}) =>
    hasQueryString ? `1px solid ${Colors.LIGHT_GRAY2}` : 'none'};
  display: flex;
  padding: 12px;
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
