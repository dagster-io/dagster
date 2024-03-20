import {Colors, Icon, IconWrapper, Spinner, UnstyledButton} from '@dagster-io/ui-components';
import Fuse from 'fuse.js';
import debounce from 'lodash/debounce';
import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components';

import {SearchInput} from './SearchDialog';
import {SearchResultItem, SearchResultsList, SearchResultsProps} from './SearchResults';
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

  const rightElement = () => {
    if (loading) {
      return <Spinner purpose="body-text" />;
    }
    if (queryString.length) {
      return (
        <ClearButton
          onMouseDown={(e: React.MouseEvent<HTMLButtonElement>) => {
            // Prevent default to avoid stealing focus from the input.
            e.preventDefault();
            dispatch({type: 'change-query', queryString: ''});
          }}
        >
          <Icon name="close" size={20} color={Colors.textDisabled()} />
        </ClearButton>
      );
    }
    return null;
  };

  return (
    <SearchInputWrapper>
      <AssetSearchBox $hasQueryString={!!queryString.length}>
        <Icon name="search" color={Colors.accentGray()} size={20} />
        <SearchInput
          data-search-input="1"
          autoFocus
          spellCheck={false}
          onChange={onChange}
          onKeyDown={onKeyDown}
          placeholder="Search assets"
          type="text"
          value={queryString}
        />
        {rightElement()}
      </AssetSearchBox>
      <SearchResultsWrapper>
        <AssetSearchResults
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

interface Props extends SearchResultsProps {
  filterResults: Fuse.FuseResult<SearchResult>[];
}

const AssetSearchResults = (props: Props) => {
  const {highlight, onClickResult, queryString, results, filterResults} = props;

  if (!results.length && !filterResults.length && queryString) {
    return <NoAssetResults>No results</NoAssetResults>;
  }

  return (
    <SearchResultsList hasResults={!!results.length || !!filterResults.length}>
      {results.map((result, ii) => (
        <SearchResultItem
          key={result.item.href}
          isHighlight={highlight === ii}
          result={result}
          onClickResult={onClickResult}
        />
      ))}
      {filterResults.length > 0 ? (
        <>
          <MatchingFiltersHeader>Matching filters</MatchingFiltersHeader>
          {filterResults.map((result, ii) => (
            <SearchResultItem
              key={result.item.href}
              isHighlight={highlight === ii + results.length}
              result={result}
              onClickResult={onClickResult}
            />
          ))}
        </>
      ) : null}
    </SearchResultsList>
  );
};

interface AssetSearchBoxProps {
  readonly $hasQueryString: boolean;
}

const AssetSearchBox = styled.div<AssetSearchBoxProps>`
  background: ${Colors.backgroundDefault()};
  border-radius: ${({$hasQueryString}) => ($hasQueryString ? '8px 8px 0 0' : '8px')};
  border: none;
  align-items: center;
  box-shadow: ${({$hasQueryString}) =>
      $hasQueryString ? Colors.keylineDefault() : Colors.borderDefault()}
    inset 0px 0px 0px 1px;
  display: flex;
  padding: 12px 16px 12px 12px;
  transition: all 100ms linear;

  :hover {
    box-shadow: ${({$hasQueryString}) =>
        $hasQueryString ? Colors.keylineDefault() : Colors.borderHover()}
      inset 0px 0px 0px 1px;
  }
`;

const ClearButton = styled(UnstyledButton)`
  ${IconWrapper} {
    transition: background-color 100ms linear;
    :hover {
      background-color: ${Colors.textDefault()};
    }
  }
`;

const SearchInputWrapper = styled.div`
  position: relative;
`;

const SearchResultsWrapper = styled.div`
  top: 48px;
  left: 1px;
  position: absolute;
  z-index: 1;
  width: calc(100% - 2px);
`;

const NoAssetResults = styled.div`
  background-color: ${Colors.backgroundDefault()};
  border-radius: 0 0 8px 8px;
  color: ${Colors.textLighter()};
  font-size: 16px;
  padding: 16px;
`;

const MatchingFiltersHeader = styled.li`
  background-color: ${Colors.backgroundDefault()};
  padding: 8px 12px;
  border-bottom: 1px solid ${Colors.backgroundGray()};
  color: ${Colors.textLight()};
  font-weight: 500;
`;
