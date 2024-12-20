// eslint-disable-next-line no-restricted-imports
import {Overlay} from '@blueprintjs/core';
import {Colors, FontFamily, Icon, Spinner, Tooltip} from '@dagster-io/ui-components';
import Fuse from 'fuse.js';
import debounce from 'lodash/debounce';
import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components';

import {SearchResults} from './SearchResults';
import {SearchResult} from './types';
import {useGlobalSearch} from './useGlobalSearch';
import {__updateSearchVisibility} from './useSearchVisibility';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {TooltipShortcutInfo, TopNavButton} from '../app/TopNavButton';
import {useTrackEvent} from '../app/analytics';

const MAX_DISPLAYED_RESULTS = 50;

type State = {
  shown: boolean;
  queryString: string;
  searching: boolean;
  primaryResults: Fuse.FuseResult<SearchResult>[];
  secondaryResults: Fuse.FuseResult<SearchResult>[];
  highlight: number;
  loaded: boolean;
};

type Action =
  | {type: 'show-dialog'}
  | {type: 'hide-dialog'}
  | {type: 'highlight'; highlight: number}
  | {type: 'change-query'; queryString: string}
  | {type: 'complete-primary'; queryString: string; results: Fuse.FuseResult<SearchResult>[]}
  | {type: 'complete-secondary'; queryString: string; results: Fuse.FuseResult<SearchResult>[]};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'show-dialog':
      return {...state, shown: true, loaded: true};
    case 'hide-dialog':
      return {...state, shown: false, queryString: '', primaryResults: [], secondaryResults: []};
    case 'highlight':
      return {...state, highlight: action.highlight};
    case 'change-query':
      return {...state, queryString: action.queryString, searching: true, highlight: 0};
    case 'complete-primary':
      // If the received results match the current querystring, use them. Otherwise discard.
      const primaryResults =
        action.queryString === state.queryString ? action.results : state.primaryResults;
      return {...state, primaryResults, searching: false};
    case 'complete-secondary':
      // If the received results match the current querystring, use them. Otherwise discard.
      const secondaryResults =
        action.queryString === state.queryString ? action.results : state.secondaryResults;
      return {...state, secondaryResults, searching: false};
    default:
      return state;
  }
};

const initialState: State = {
  shown: false,
  queryString: '',
  searching: false,
  primaryResults: [],
  secondaryResults: [],
  highlight: 0,
  loaded: false,
};

const DEBOUNCE_MSEC = 100;

// sort by Fuse score ascending, lower is better
const sortResultsByFuseScore = (
  a: Fuse.FuseResult<SearchResult>,
  b: Fuse.FuseResult<SearchResult>,
) => {
  return (a.score ?? 0) - (b.score ?? 0);
};

export const SearchDialog = () => {
  const history = useHistory();
  const {initialize, loading, searchPrimary, searchSecondary} = useGlobalSearch({
    searchContext: 'global',
  });
  const trackEvent = useTrackEvent();

  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {shown, queryString, primaryResults, secondaryResults, highlight} = state;

  const {renderedResults, numRenderedResults} = React.useMemo(() => {
    const results = [...primaryResults, ...secondaryResults].sort(sortResultsByFuseScore);
    const renderedResults = results.slice(0, MAX_DISPLAYED_RESULTS);
    return {renderedResults, numRenderedResults: renderedResults.length};
  }, [primaryResults, secondaryResults]);

  const openSearch = React.useCallback(() => {
    trackEvent('open-global-search');
    trackEvent('searchOpen');
    initialize();
    dispatch({type: 'show-dialog'});
  }, [initialize, trackEvent]);

  React.useEffect(() => {
    __updateSearchVisibility(shown);
  }, [shown]);

  const searchAndHandlePrimary = React.useCallback(
    async (queryString: string) => {
      const {queryString: queryStringForResults, results} = await searchPrimary(queryString);
      dispatch({type: 'complete-primary', queryString: queryStringForResults, results});
    },
    [searchPrimary],
  );

  const searchAndHandleSecondary = React.useCallback(
    async (queryString: string) => {
      const {queryString: queryStringForResults, results} = await searchSecondary(queryString);
      dispatch({type: 'complete-secondary', queryString: queryStringForResults, results});
    },
    [searchSecondary],
  );

  const debouncedSearch = React.useMemo(() => {
    return debounce(async (queryString: string) => {
      searchAndHandlePrimary(queryString);
      searchAndHandleSecondary(queryString);
    }, DEBOUNCE_MSEC);
  }, [searchAndHandlePrimary, searchAndHandleSecondary]);

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    dispatch({type: 'change-query', queryString: newValue});
    debouncedSearch(newValue);
  };

  const onClickResult = React.useCallback(
    (result: Fuse.FuseResult<SearchResult>) => {
      dispatch({type: 'hide-dialog'});
      history.push(result.item.href);
    },
    [history],
  );

  const shortcutFilter = React.useCallback((e: KeyboardEvent) => {
    if (e.altKey || e.shiftKey) {
      return false;
    }

    if (e.ctrlKey || e.metaKey) {
      return e.code === 'KeyK';
    }

    return e.code === 'Slash';
  }, []);

  const highlightedResult = renderedResults[highlight] || null;

  const onKeyDown = (e: React.KeyboardEvent) => {
    const {key} = e;
    if (key === 'Escape') {
      dispatch({type: 'hide-dialog'});
      return;
    }

    if (!numRenderedResults) {
      return;
    }

    const lastResult = numRenderedResults - 1;

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
          history.push(highlightedResult.item.href);
        }
    }
  };

  return (
    <>
      <ShortcutHandler onShortcut={openSearch} shortcutLabel="/" shortcutFilter={shortcutFilter}>
        <Tooltip
          content={<TooltipShortcutInfo label="Search" shortcutKey="/" />}
          placement="bottom"
        >
          <TopNavButton onClick={openSearch}>
            <Icon name="search" size={20} />
          </TopNavButton>
        </Tooltip>
      </ShortcutHandler>
      <Overlay
        backdropProps={{style: {backgroundColor: Colors.dialogBackground()}}}
        isOpen={shown}
        onClose={() => dispatch({type: 'hide-dialog'})}
        transitionDuration={100}
      >
        <Container>
          <SearchBox $hasQueryString={!!queryString.length}>
            <Icon name="search" color={Colors.accentGray()} size={20} />
            <SearchInput
              data-search-input="1"
              autoFocus
              spellCheck={false}
              onChange={onChange}
              onKeyDown={onKeyDown}
              placeholder="Search assets, jobs, schedules, sensors…"
              type="text"
              value={queryString}
            />
            {loading ? <Spinner purpose="body-text" /> : null}
          </SearchBox>
          <SearchResults
            highlight={highlight}
            queryString={queryString}
            results={renderedResults}
            onClickResult={onClickResult}
            searching={loading || state.searching}
          />
        </Container>
      </Overlay>
    </>
  );
};

const Container = styled.div`
  background-color: ${Colors.backgroundDefault()};
  border-radius: 8px;
  box-shadow:
    2px 2px 8px ${Colors.shadowDefault()},
    ${Colors.keylineDefault()} inset 0px 0px 0px 1px;
  max-height: 60vh;
  left: calc(50% - 300px);
  overflow: hidden;
  width: 600px;
  top: 20vh;
`;

export interface SearchBoxProps {
  readonly $hasQueryString: boolean;
}

export const SearchBox = styled.div<SearchBoxProps>`
  background: ${Colors.backgroundDefault()};
  border-radius: ${({$hasQueryString}) => ($hasQueryString ? '8px 8px 0 0' : '8px')};
  border: none;
  align-items: center;
  box-shadow: ${({$hasQueryString}) =>
      $hasQueryString ? Colors.keylineDefault() : Colors.borderDefault()}
    inset 0px 0px 0px 1px;
  display: flex;
  padding: 12px 20px 12px 12px;
  transition: all 100ms linear;

  :hover {
    box-shadow: ${({$hasQueryString}) =>
        $hasQueryString ? Colors.keylineDefault() : Colors.borderHover()}
      0 0 0 1px inset;
  }
`;

export const SearchInput = styled.input`
  background-color: transparent;
  border: none;
  color: ${Colors.textDefault()};
  font-family: ${FontFamily.default};
  font-size: 18px;
  margin-left: 4px;
  outline: none;
  width: 100%;

  &::placeholder {
    color: ${Colors.textDisabled()};
  }

  ::focus {
    outline: none;
  }
`;
