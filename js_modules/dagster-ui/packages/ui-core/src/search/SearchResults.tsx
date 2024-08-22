import {
  Box,
  Caption,
  CaptionBolded,
  Colors,
  Icon,
  IconName,
  StyledTag,
} from '@dagster-io/ui-components';
import Fuse from 'fuse.js';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {
  AssetFilterSearchResultType,
  SearchResult,
  SearchResultType,
  isAssetFilterSearchResultType,
} from './types';
import {assertUnreachable} from '../app/Util';
import {isCanonicalComputeKindTag, isCanonicalStorageKindTag} from '../graph/KindTags';
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
    case AssetFilterSearchResultType.StorageKind:
      return 'storage_kind';
    case SearchResultType.Page:
      return 'source';
    case AssetFilterSearchResultType.Column:
      return 'view_column';
    default:
      assertUnreachable(type);
  }
};

const assetFilterPrefixString = (type: AssetFilterSearchResultType): string => {
  switch (type) {
    case AssetFilterSearchResultType.CodeLocation:
      return 'Code location';
    case AssetFilterSearchResultType.Kind:
      return 'Compute kind';
    case AssetFilterSearchResultType.Tag:
      return 'Tag';
    case AssetFilterSearchResultType.Owner:
      return 'Owner';
    case AssetFilterSearchResultType.AssetGroup:
      return 'Group';
    case AssetFilterSearchResultType.StorageKind:
      return 'Storage kind';
    case AssetFilterSearchResultType.Column:
      return 'Column';
    default:
      assertUnreachable(type);
  }
};

type ResultType = Fuse.FuseResult<SearchResult> | Pick<Fuse.FuseResult<SearchResult>, 'item'>;
type ItemProps<T extends ResultType> = {
  isHighlight: boolean;
  onClickResult: (result: T) => void;
  result: T;
};

function buildSearchLabel(result: Fuse.FuseResult<SearchResult>): JSX.Element[] {
  // Fuse provides indices of the label that match the query string.
  // Use these match indices to display the label with the matching parts bolded.

  let longestMatch: Fuse.RangeTuple | undefined;
  // Only bold longest match
  if (result.matches && result.matches.length > 0) {
    const match = result.matches[0]!; // Only one match per row, since we only match by label

    if (match.indices.length > 0) {
      longestMatch = match.indices[0]!;
      for (let i = 1; i < match.indices.length; i++) {
        const current: [number, number] = match.indices[i]!;
        if (current[1] - current[0] > longestMatch[1]! - longestMatch[0]!) {
          longestMatch = current;
        }
      }
    }
  }

  const labelComponents = [];
  let parsedString = '';
  if (longestMatch) {
    const stringBeforeMatch = result.item.label.slice(parsedString.length, longestMatch[0]);
    labelComponents.push(<Caption>{stringBeforeMatch}</Caption>);
    parsedString += stringBeforeMatch;

    const match = result.item.label.slice(longestMatch[0], longestMatch[1] + 1);
    labelComponents.push(<CaptionBolded>{match}</CaptionBolded>);
    parsedString += match;
  }

  const stringAfterMatch = result.item.label.substring(parsedString.length);
  labelComponents.push(<Caption>{stringAfterMatch}</Caption>);
  parsedString += stringAfterMatch;

  return labelComponents;
}

function buildSearchIcons(item: SearchResult, isHighlight: boolean): JSX.Element[] {
  const icons = [];

  if (item.type === SearchResultType.Asset) {
    const computeKindTag = item.tags?.find(isCanonicalComputeKindTag);
    if (computeKindTag && KNOWN_TAGS[computeKindTag.value]) {
      const computeKindSearchIcon = <TagIcon label={computeKindTag.value} />;

      icons.push(computeKindSearchIcon);
    }

    const storageKindTag = item.tags?.find(isCanonicalStorageKindTag);
    if (storageKindTag && KNOWN_TAGS[storageKindTag.value]) {
      const storageKindSearchIcon = <TagIcon label={storageKindTag.value} />;

      icons.push(storageKindSearchIcon);
    }
  }

  if (item.type === AssetFilterSearchResultType.Kind) {
    if (KNOWN_TAGS[item.label]) {
      const computeKindSearchIcon = <TagIcon label={item.label} />;

      icons.push(computeKindSearchIcon);
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

  const labelComponents = 'refIndex' in result ? buildSearchLabel(result) : [<>{item.label}</>];

  return (
    <Item isHighlight={isHighlight} ref={element}>
      <ResultLink to={item.href} onMouseDown={onClick}>
        <Box flex={{direction: 'row', alignItems: 'center', grow: 1}}>
          <StyledTag
            $fillColor={Colors.backgroundGray()}
            $interactive={false}
            $textColor={Colors.textDefault()}
          >
            <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
              {buildSearchIcons(item, isHighlight)}
              {isAssetFilterSearchResultType(item.type) && (
                <Caption>{assetFilterPrefixString(item.type)}:</Caption>
              )}
              <div>{labelComponents}</div>
              {item.repoPath && <Caption>in {item.repoPath}</Caption>}
            </Box>
          </StyledTag>
          <div style={{marginLeft: '8px'}}>
            <Description isHighlight={isHighlight}>
              {item.numResults ? `${item.numResults} assets` : item.description}
            </Description>
          </div>
        </Box>
      </ResultLink>
    </Item>
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
  const {highlight, onClickResult, queryString, results, searching} = props;

  if (!results.length && queryString) {
    if (searching) {
      return;
    }
    return <NoResults>No results</NoResults>;
  }

  return (
    <SearchResultsList hasResults={!!results.length}>
      {results.map((result, ii) => (
        <SearchResultItem
          key={result.item.href}
          isHighlight={highlight === ii}
          result={result}
          onClickResult={onClickResult}
        />
      ))}
    </SearchResultsList>
  );
};

export const NoResults = styled.div`
  color: ${Colors.textLighter()};
  font-size: 16px;
  padding: 16px;
`;

interface SearchResultsListProps {
  hasResults: boolean;
}

export const SearchResultsList = styled.ul<SearchResultsListProps>`
  max-height: calc(60vh - 48px);
  margin: 0;
  padding: ${({hasResults}) => (hasResults ? '4px 0' : 'none')};
  list-style: none;
  overflow-y: auto;
  background-color: ${Colors.backgroundDefault()};
  box-shadow: 2px 2px 8px ${Colors.shadowDefault()};
  border-radius: 0 0 4px 4px;
`;

interface HighlightableTextProps {
  readonly isHighlight: boolean;
}

const Item = styled.li<HighlightableTextProps>`
  align-items: center;
  background-color: ${({isHighlight}) =>
    isHighlight ? Colors.backgroundLightHover() : Colors.backgroundDefault()};
  box-shadow: ${({isHighlight}) => (isHighlight ? Colors.accentBlue() : 'transparent')} 4px 0 0
    inset;
  color: ${Colors.textLight()};
  display: flex;
  flex-direction: row;
  list-style: none;
  margin: 0;
  user-select: none;

  &:hover {
    background-color: ${Colors.backgroundLighter()};
  }
`;

const ResultLink = styled(Link)`
  align-items: center;
  align-self: stretch;
  display: flex;
  flex-direction: row;
  padding: 8px 12px;
  text-decoration: none;
  width: 100%;

  &:hover {
    text-decoration: none;
  }
`;

const Description = styled.div<HighlightableTextProps>`
  color: ${({isHighlight}) => (isHighlight ? Colors.textDefault() : Colors.textLight())};
  font-size: 12px;
  max-width: 530px;
  overflow-x: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;
