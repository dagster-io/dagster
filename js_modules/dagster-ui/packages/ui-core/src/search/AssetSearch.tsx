import {Colors, FontFamily, Icon, Spinner} from '@dagster-io/ui-components';
import Fuse from 'fuse.js';
import debounce from 'lodash/debounce';
import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components';

import {SearchBoxProps} from './SearchDialog';
import {SearchResults} from './SearchResults';
import {SearchResult, SearchResultType, isAssetFilterSearchResultType} from './types';
import {useGlobalSearch} from './useGlobalSearch';
import {Trace, createTrace} from '../performance';

const MAX_ASSET_RESULTS = 50;
const MAX_FILTER_RESULTS = 25;

type State = {
  queryString: string;
  searching: boolean;
  secondaryResults: Fuse.FuseResult<SearchResult>[];
  highlight: number;
};

type Action =
  | {type: 'highlight'; highlight: number}
  | {type: 'change-query'; queryString: string}
  | {type: 'complete-secondary'; queryString: string; results: Fuse.FuseResult<SearchResult>[]};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'highlight':
      return {...state, highlight: action.highlight};
    case 'change-query':
      return {...state, queryString: action.queryString, searching: true, highlight: 0};
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
  queryString: '',
  searching: false,
  secondaryResults: [],
  highlight: 0,
};

const DEBOUNCE_MSEC = 100;

type SearchResultGroups = {
  assetResults: Fuse.FuseResult<SearchResult>[];
  assetFilterResults: Fuse.FuseResult<SearchResult>[];
};

function groupSearchResults(secondaryResults: Fuse.FuseResult<SearchResult>[]): SearchResultGroups {
  return {
    assetResults: secondaryResults.filter((result) => result.item.type === SearchResultType.Asset),
    assetFilterResults: secondaryResults.filter((result) =>
      isAssetFilterSearchResultType(result.item.type),
    ),
  };
}

export const AssetSearch = () => {
  const history = useHistory();
  const {loading, searchSecondary, initialize} = useGlobalSearch({
    includeAssetFilters: true,
  });

  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {queryString, secondaryResults, highlight} = state;

  const {assetResults, assetFilterResults} = groupSearchResults(secondaryResults);

  const renderedAssetResults = assetResults.slice(0, MAX_ASSET_RESULTS);
  const renderedFilterResults = assetFilterResults.slice(0, MAX_FILTER_RESULTS);

  const renderedResults = [...renderedAssetResults, ...renderedFilterResults];
  const numRenderedResults = renderedResults.length;

  const isFirstSearch = React.useRef(true);
  const firstSearchTrace = React.useRef<null | Trace>(null);

  React.useEffect(() => {
    initialize();
    if (!loading && secondaryResults) {
      firstSearchTrace.current?.endTrace();
    }
  }, [loading, secondaryResults, initialize]);

  const searchAndHandleSecondary = React.useCallback(
    async (queryString: string) => {
      const {queryString: queryStringForResults, results} = await searchSecondary(queryString);
      dispatch({type: 'complete-secondary', queryString: queryStringForResults, results});
    },
    [searchSecondary],
  );

  const debouncedSearch = React.useMemo(() => {
    const debouncedSearch = debounce(async (queryString: string) => {
      searchAndHandleSecondary(queryString);
    }, DEBOUNCE_MSEC);
    return (queryString: string) => {
      if (!firstSearchTrace.current && isFirstSearch.current) {
        isFirstSearch.current = false;
        const trace = createTrace('AssetSearch:FirstSearch');
        firstSearchTrace.current = trace;
        trace.startTrace();
      }
      return debouncedSearch(queryString);
    };
  }, [searchAndHandleSecondary]);

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    dispatch({type: 'change-query', queryString: newValue});
    debouncedSearch(newValue);
  };

  const onClickResult = React.useCallback(
    (result: Fuse.FuseResult<SearchResult>) => {
      history.push(result.item.href);
    },
    [history],
  );

  const highlightedResult = renderedResults[highlight] || null;

  const onKeyDown = (e: React.KeyboardEvent) => {
    const {key} = e;

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
          history.push(highlightedResult.item.href);
        }
    }
  };

  return (
    <SearchInputWrapper>
      <AssetSearchBox hasQueryString={!!queryString.length}>
        <Icon name="search" color={Colors.accentGray()} size={20} />
        <AssetSearchInput
          data-search-input="1"
          autoFocus
          spellCheck={false}
          onChange={onChange}
          onKeyDown={onKeyDown}
          placeholder="Search assets"
          type="text"
          value={queryString}
        />
        {loading ? <Spinner purpose="body-text" /> : null}
      </AssetSearchBox>
      <SearchResultsWrapper>
        <SearchResults
          highlight={highlight}
          queryString={queryString}
          results={renderedAssetResults}
          filterResults={renderedFilterResults}
          onClickResult={onClickResult}
        />
      </SearchResultsWrapper>
    </SearchInputWrapper>
  );
};

const AssetSearchBox = styled.div<SearchBoxProps>`
  border-radius: 8px;
  align-items: center;
  border: ${({hasQueryString}) =>
    hasQueryString ? `1px solid ${Colors.borderHover()}` : `1px solid ${Colors.borderDefault()}`};
  display: flex;
  padding: 12px 20px 12px 12px;
  transition: all 100ms linear;
  background: ${Colors.backgroundDefaultHover()};

  :hover {
    border: 1px solid ${Colors.borderHover()};
    background: ${Colors.backgroundDefault()};
  }
`;

const AssetSearchInput = styled.input`
  border: none;
  color: ${Colors.textDefault()};
  font-family: ${FontFamily.default};
  font-size: 18px;
  margin-left: 4px;
  outline: none;
  width: 100%;
  background-color: transparent;

  &::placeholder {
    color: ${Colors.textDisabled()};
  }
`;

const SearchInputWrapper = styled.div`
  position: relative;
`;

const SearchResultsWrapper = styled.div`
  top: 60px;
  position: absolute;
  z-index: 1;
  width: 100%;
`;
