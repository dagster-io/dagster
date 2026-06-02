import {
  BaseTag,
  Box,
  Caption,
  CaptionBolded,
  Colors,
  Icon,
  IconName,
} from '@dagster-io/ui-components';
import clsx from 'clsx';
import Fuse from 'fuse.js';
import * as React from 'react';
import {ReactNode} from 'react';
import {Link} from 'react-router-dom';

import styles from './css/SearchResults.module.css';
import {
  AssetFilterSearchResultType,
  SearchResult,
  SearchResultType,
  isAssetFilterSearchResultType,
} from './types';
import {assertUnreachable} from '../app/Util';
import {isCanonicalComputeKindTag} from '../graph/KindTags';
import {KNOWN_TAGS, TagIcon} from '../graph/OpTags';

const iconForType = (type: SearchResultType | AssetFilterSearchResultType): IconName => {
  switch (type) {
    case SearchResultType.Asset:
      return 'asset';
    case SearchResultType.AssetGroup:
      return 'asset_group';
    case SearchResultType.PartitionSet:
    case SearchResultType.Schedule:
      return 'schedule';
    case SearchResultType.Pipeline:
      return 'job';
    case SearchResultType.Repository:
      return 'source';
    case SearchResultType.Run:
      return 'history';
    case SearchResultType.Sensor:
      return 'sensors';
    case SearchResultType.Solid:
      return 'op';
    case SearchResultType.Resource:
      return 'resource';
    case AssetFilterSearchResultType.CodeLocation:
      return 'folder';
    case AssetFilterSearchResultType.Owner:
      return 'account_circle';
    case AssetFilterSearchResultType.AssetGroup:
      return 'asset_group';
    case AssetFilterSearchResultType.Kind:
      return 'compute_kind';
    case AssetFilterSearchResultType.Tag:
      return 'tag';
    case SearchResultType.Page:
      return 'source';
    case AssetFilterSearchResultType.Column:
      return 'view_column';
    case AssetFilterSearchResultType.ColumnTag:
      return 'tag';
    case AssetFilterSearchResultType.TableName:
      return 'database';
    default:
      assertUnreachable(type);
  }
};

const assetFilterPrefixString = (type: AssetFilterSearchResultType): string => {
  switch (type) {
    case AssetFilterSearchResultType.CodeLocation:
      return 'Code location';
    case AssetFilterSearchResultType.Kind:
      return 'Kind';
    case AssetFilterSearchResultType.Tag:
      return 'Tag';
    case AssetFilterSearchResultType.Owner:
      return 'Owner';
    case AssetFilterSearchResultType.AssetGroup:
      return 'Group';
    case AssetFilterSearchResultType.Column:
      return 'Column';
    case AssetFilterSearchResultType.ColumnTag:
      return 'Column tag';
    case AssetFilterSearchResultType.TableName:
      return 'Table name';
    default:
      assertUnreachable(type);
  }
};

type ResultType = Fuse.FuseResult<SearchResult> | Pick<Fuse.FuseResult<SearchResult>, 'item'>;
type ItemProps<T extends ResultType> = {
  isHighlight: boolean;
  onClickResult: (result: T) => void;
  queryString: string;
  result: T;
};

function buildSearchLabel(result: Fuse.FuseResult<SearchResult>, queryString: string): ReactNode {
  const queryStringLower = queryString.toLowerCase();
  const {label} = result.item;
  const exactMatchPosition = label.indexOf(queryStringLower);

  if (exactMatchPosition === -1) {
    return <Caption>{result.item.label}</Caption>;
  }

  const stringBeforeMatch = label.slice(0, exactMatchPosition);
  const match = label.slice(exactMatchPosition, exactMatchPosition + queryString.length);
  const stringAfterMatch = label.slice(exactMatchPosition + queryString.length);

  return (
    <>
      <Caption>{stringBeforeMatch}</Caption>
      <CaptionBolded>{match}</CaptionBolded>
      <Caption>{stringAfterMatch}</Caption>
    </>
  );
}

function buildSearchIcons(item: SearchResult, isHighlight: boolean): JSX.Element[] {
  const icons = [];

  if (item.type === SearchResultType.Asset) {
    const computeKindTag = item.tags?.find(isCanonicalComputeKindTag);
    if (computeKindTag && KNOWN_TAGS.hasOwnProperty(computeKindTag.value)) {
      const computeKindSearchIcon = <TagIcon label={computeKindTag.value} />;

      icons.push(computeKindSearchIcon);
    }
  }

  if (item.type === AssetFilterSearchResultType.Kind) {
    if (KNOWN_TAGS.hasOwnProperty(item.label)) {
      const kindSearchIcon = <TagIcon label={item.label} />;

      icons.push(kindSearchIcon);
    }
  }

  if (icons.length === 0) {
    const defaultSearchIcon = (
      <Icon
        name={iconForType(item.type)}
        color={isHighlight ? Colors.textDefault() : Colors.textLight()}
      />
    );

    icons.push(defaultSearchIcon);
  }

  return icons;
}

export const SearchResultItem = <T extends ResultType>({
  isHighlight,
  onClickResult,
  queryString,
  result,
}: ItemProps<T>) => {
  const {item} = result;
  const element = React.useRef<HTMLLIElement>(null);

  React.useEffect(() => {
    if (element.current && isHighlight) {
      element.current.scrollIntoView({block: 'nearest'});
    }
  }, [isHighlight]);

  const onClick = React.useCallback(
    (e: React.MouseEvent) => {
      if (!e.getModifierState('Meta') && !e.getModifierState('Control')) {
        e.preventDefault();
        onClickResult(result);
      }
    },
    [onClickResult, result],
  );

  const labelComponents = 'refIndex' in result ? buildSearchLabel(result, queryString) : item.label;

  return (
    <li className={clsx(styles.item, isHighlight && styles.highlight)} ref={element}>
      <Link className={styles.resultLink} to={item.href} onMouseDown={onClick}>
        <Box
          flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12}}
          style={{width: '100%'}}
        >
          <Box flex={{direction: 'row', alignItems: 'center', grow: 1}}>
            <BaseTag
              fillColor={Colors.backgroundGray()}
              textColor={Colors.textDefault()}
              tooltipText={item.label}
              icon={
                <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}} margin={{right: 4}}>
                  {buildSearchIcons(item, isHighlight)}
                </Box>
              }
              label={
                <>
                  {isAssetFilterSearchResultType(item.type) && (
                    <Caption>{assetFilterPrefixString(item.type)}:</Caption>
                  )}
                  {labelComponents}
                  {item.repoPath ? <Caption> in {item.repoPath}</Caption> : null}
                </>
              }
            />
            <div style={{marginLeft: '8px'}}>
              <div className={clsx(styles.description, isHighlight && styles.highlight)}>
                {item.numResults ? `${item.numResults} assets` : item.description}
              </div>
            </div>
          </Box>
          <Box
            className={styles.resultEnterWrapper}
            flex={{direction: 'row', gap: 8, alignItems: 'center'}}
          >
            <div>Enter</div>
            <Icon name="key_return" color={Colors.accentGray()} />
          </Box>
        </Box>
      </Link>
    </li>
  );
};

export type SearchResultsProps<T extends ResultType> = {
  highlight: number;
  onClickResult: (result: T) => void;
  queryString: string;
  results: T[];
  searching: boolean;
};

export const SearchResults = <T extends ResultType>(props: SearchResultsProps<T>) => {
  const {highlight, onClickResult, queryString, results: _results, searching} = props;

  // Our fuse worker returns all results if we put in an empty string.
  // This is to support AssetSearch in Cloud which allows showing all results for a particular filter.
  // For OSS we don't want any results if the queryString is null so lets make the results an empty list in that
  // case here
  const results = queryString ? _results : [];

  if (!results.length && queryString) {
    if (searching) {
      return;
    }
    return <div className={styles.noResults}>No results</div>;
  }

  return (
    <ul className={clsx(styles.searchResultsList, !!results.length && styles.hasResults)}>
      {results.map((result, ii) => (
        <SearchResultItem
          key={result.item.href}
          isHighlight={highlight === ii}
          queryString={queryString}
          result={result}
          onClickResult={onClickResult}
        />
      ))}
    </ul>
  );
};
