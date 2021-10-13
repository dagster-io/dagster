import Fuse from 'fuse.js';
import memoize from 'lodash/memoize';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';
import {Popover} from '../ui/Popover';
import {TextInput} from '../ui/TextInput';
import {useSuggestionsForString} from '../ui/useSuggestionsForString';

import {Asset} from './AssetsCatalogTable';

const getAssetFilterProviders = memoize((assets: Asset[] = []) => {
  const allTags = {};
  assets.forEach((asset) => {
    asset.tags.forEach((tag) => {
      allTags[tag.key] = tag.value;
    });
  });
  const tagList: string[] = [];
  Object.keys(allTags).forEach((key) => {
    tagList.push(`${key}=${allTags[key]}`);
  });
  tagList.sort();

  if (!tagList.length) {
    return [];
  }

  return [
    {
      token: 'tag',
      values: () => tagList,
    },
  ];
});

export const filterAssets = (assets: Asset[], query?: string) => {
  if (!query) {
    return assets;
  }

  const tokens = query.split(/\s+/);
  const tagFilters = tokens
    .filter((token) => token.startsWith('tag:'))
    .map((s) => {
      const [key, value] = s.substring(4).split('=');
      return {key, value};
    });
  const assetKeyFilters = tokens.filter((token) => !token.startsWith('tag:'));

  return assets
    .filter((asset) => textMatches(asset.key.path.join(' '), assetKeyFilters.join(' ')))
    .filter((asset) =>
      tagFilters.every((filterTag) =>
        asset.tags.some(
          (assetTag) => assetTag.key === filterTag.key && assetTag.value === filterTag.value,
        ),
      ),
    );
};

const textMatches = (haystack: string, needle: string) =>
  needle
    .toLowerCase()
    .split(' ')
    .filter((x) => x)
    .every((word) => haystack.toLowerCase().includes(word));

const fuseOptions = {threshold: 0.3};

export const AssetsFilter = ({
  assets,
  query,
  onSetQuery,
}: {
  assets: Asset[];
  query: string | undefined;
  onSetQuery: (query: string) => void;
}) => {
  const [highlight, setHighlight] = React.useState<number>(0);
  const [shown, setShown] = React.useState<boolean>(false);

  const suggestionProviders = getAssetFilterProviders(assets);
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

  const {suggestions, onSelectSuggestion} = useSuggestionsForString(buildSuggestions, query || '');
  const onSelect = React.useCallback(
    (suggestion: string) => {
      onSetQuery(onSelectSuggestion(suggestion));
      setHighlight(0);
    },
    [onSetQuery, onSelectSuggestion],
  );

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    // Enter and Return confirm the currently selected suggestion or
    // confirm the freeform text you've typed if no suggestions are shown.
    if (e.key === 'Enter' || e.key === 'Return' || e.key === 'Tab') {
      if (suggestions.length) {
        const picked = suggestions[highlight];
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
      setHighlight(0);
      return;
    }

    const lastResult = suggestions.length - 1;
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlight(highlight === 0 ? lastResult : highlight - 1);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlight(highlight === lastResult ? 0 : highlight + 1);
    }
  };

  const onChange = (e: React.ChangeEvent<any>) => {
    onSetQuery(e.target.value);
    setHighlight(0);
  };

  const isOpen = shown && suggestions.length > 0;
  return (
    <Popover
      minimal
      usePortal
      isOpen={isOpen}
      position="bottom-left"
      content={
        <Menu>
          {suggestions.map((suggestion, idx) => (
            <Item
              key={idx}
              onMouseDown={(e: React.MouseEvent<any>) => {
                e.preventDefault();
                e.stopPropagation();
                onSelect(suggestion);
              }}
              isHighlight={highlight === idx}
            >
              <div>
                <div>{suggestion}</div>
              </div>
            </Item>
          ))}
        </Menu>
      }
    >
      <TextInput
        value={query}
        style={{width: '300px'}}
        placeholder="Filter asset keys…"
        onChange={onChange}
        onKeyDown={onKeyDown}
        onBlur={() => setShown(false)}
        onFocus={() => setShown(true)}
      />
    </Popover>
  );
};

const Menu = styled.ul`
  list-style: none;
  margin: 0;
  max-height: 200px;
  max-width: 800px;
  min-width: 600px;
  overflow-y: auto;
  padding: 0;
`;
const Item = styled.li<{
  readonly isHighlight: boolean;
}>`
  align-items: center;
  background-color: ${({isHighlight}) => (isHighlight ? ColorsWIP.Blue500 : ColorsWIP.White)};
  color: ${({isHighlight}) => (isHighlight ? ColorsWIP.White : 'default')};
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
    background-color: ${({isHighlight}) => (isHighlight ? ColorsWIP.Blue500 : ColorsWIP.Gray100)};
  }
`;
