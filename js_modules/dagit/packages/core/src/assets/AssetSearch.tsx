import Fuse from 'fuse.js';
import * as React from 'react';
import {useHistory} from 'react-router-dom';

import {SearchResults} from '../search/SearchResults';
import {SearchResult} from '../search/types';
import {useAssetSearch} from '../search/useRepoSearch';
import {MenuWIP} from '../ui/Menu';
import {Popover} from '../ui/Popover';
import {Spinner} from '../ui/Spinner';
import {TextInput} from '../ui/TextInput';

type State = {
  open: boolean;
  queryString: string;
  results: Fuse.FuseResult<SearchResult>[];
  highlight: number;
};

type Action =
  | {type: 'open'}
  | {type: 'close'}
  | {type: 'highlight'; highlight: number}
  | {type: 'change-query'; queryString: string}
  | {type: 'complete-search'; results: Fuse.FuseResult<SearchResult>[]};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'open':
      return {...state, open: true};
    case 'close':
      return {...state, open: false, queryString: '', highlight: 0};
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
  open: false,
  queryString: '',
  results: [],
  highlight: 0,
};

export const AssetSearch = () => {
  const history = useHistory();
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {open, queryString, results, highlight} = state;
  const {loading, performSearch} = useAssetSearch();

  React.useEffect(() => {
    const results = performSearch(queryString);
    dispatch({type: 'complete-search', results});
  }, [queryString, performSearch]);

  const onSelect = React.useCallback(
    (result: Fuse.FuseResult<SearchResult>) => {
      dispatch({type: 'close'});
      history.push(result.item.href);
    },
    [history],
  );

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    // Enter and Return confirm the currently selected suggestion or
    // confirm the freeform text you've typed if no suggestions are shown.
    if (e.key === 'Enter' || e.key === 'Return' || e.key === 'Tab') {
      if (results.length) {
        const picked = results[highlight];
        if (!picked) {
          throw new Error('Selection out of sync with suggestions');
        }
        onSelect(picked);
        e.preventDefault();
        e.stopPropagation();
      }
      return;
    }

    // Escape closes the options. The options re-open if you type another char or click.
    if (e.key === 'Escape') {
      dispatch({type: 'close'});
      return;
    }

    const lastResult = results.length - 1;
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      dispatch({type: 'highlight', highlight: highlight === 0 ? lastResult : highlight - 1});
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      dispatch({type: 'highlight', highlight: highlight === lastResult ? 0 : highlight + 1});
    }
  };

  return (
    <div style={{width: 600}}>
      <Popover
        minimal
        fill={true}
        isOpen={open && results.length > 0}
        position={'bottom-left'}
        content={
          <MenuWIP style={{maxWidth: 600, minWidth: 600}}>
            {loading ? <Spinner purpose="body-text" /> : null}
            <SearchResults
              highlight={highlight}
              queryString={queryString}
              results={results.slice(0, 10)}
              onClickResult={onSelect}
            />
          </MenuWIP>
        }
      >
        <TextInput
          value={queryString}
          style={{width: '600px'}}
          placeholder={`Search all asset_keys...`}
          onChange={(e: React.ChangeEvent<any>) =>
            dispatch({type: 'change-query', queryString: e.target.value})
          }
          onFocus={() => dispatch({type: 'open'})}
          onBlur={() => dispatch({type: 'close'})}
          onKeyDown={onKeyDown}
        />
      </Popover>
    </div>
  );
};
