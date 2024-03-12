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
    default:
      return 'source';
  }
};

const assetFilterPrefixString = (type: AssetFilterSearchResultType): string => {
  switch (type) {
    case AssetFilterSearchResultType.CodeLocation:
      return 'Code location';
    case AssetFilterSearchResultType.ComputeKind:
      return 'Compute kind';
    case AssetFilterSearchResultType.Owner:
      return 'Owner';
    case AssetFilterSearchResultType.AssetGroup:
      return 'Group';
    default:
      return '';
  }
};

interface ItemProps {
  isHighlight: boolean;
  onClickResult: (result: Fuse.FuseResult<SearchResult>) => void;
  result: Fuse.FuseResult<SearchResult>;
}

function buildSearchLabel(result: Fuse.FuseResult<SearchResult>): JSX.Element[] {
  // Fuse provides indices of the label that match the query string.
  // Use these match indices to display the label with the matching parts bolded.

  // Match indices can overlap, i.e. [0, 4] and [1, 1] can both be matches
  // So we merge them to be non-overlapping
  const mergedIndices: Fuse.RangeTuple[] = [];
  if (result.matches && result.matches.length > 0) {
    const match = result.matches[0]!; // Only one match per row, since we only match by label

    // The indices should be returned in sorted order, but we sort just in case
    const sortedIndices = Array.from(match.indices).sort((a, b) => (a[0] < b[0] ? -1 : 1));
    // Merge overlapping indices
    if (sortedIndices.length > 0) {
      mergedIndices.push(sortedIndices[0]!);
      for (let i = 1; i < sortedIndices.length; i++) {
        const last = mergedIndices[mergedIndices.length - 1]!;
        const current = sortedIndices[i]!;
        if (current[0] <= last[1]) {
          last[1] = Math.max(last[1], current[1]);
        } else {
          mergedIndices.push(current);
        }
      }
    }
  }

  const labelComponents = [];
  let parsedString = '';
  mergedIndices.forEach((indices) => {
    const stringBeforeMatch = result.item.label.slice(parsedString.length, indices[0]);
    labelComponents.push(<Caption>{stringBeforeMatch}</Caption>);
    parsedString += stringBeforeMatch;

    const match = result.item.label.slice(indices[0], indices[1] + 1);
    labelComponents.push(<CaptionBolded>{match}</CaptionBolded>);
    parsedString += match;
  });

  const stringAfterMatch = result.item.label.substring(parsedString.length);
  labelComponents.push(<Caption>{stringAfterMatch}</Caption>);
  parsedString += stringAfterMatch;

  return labelComponents;
}

const SearchResultItem = React.memo(({isHighlight, onClickResult, result}: ItemProps) => {
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

  const labelComponents = buildSearchLabel(result);

  return (
    <Item isHighlight={isHighlight} ref={element}>
      <ResultLink to={item.href} onMouseDown={onClick}>
        <Box flex={{direction: 'row', alignItems: 'center', grow: 1}}>
          <StyledTag
            $fillColor={Colors.backgroundGray()}
            $interactive={false}
            $textColor={Colors.textDefault()}
          >
            <Icon
              name={iconForType(item.type)}
              color={isHighlight ? Colors.textDefault() : Colors.textLight()}
            />
            {isAssetFilterSearchResultType(item.type) && (
              <Caption>{assetFilterPrefixString(item.type)}:&nbsp;</Caption>
            )}
            {labelComponents.map((component) => component)}
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
});

interface Props {
  highlight: number;
  onClickResult: (result: Fuse.FuseResult<SearchResult>) => void;
  queryString: string;
  results: Fuse.FuseResult<SearchResult>[];
  filterResults: Fuse.FuseResult<SearchResult>[];
}

export const SearchResults = (props: Props) => {
  const {highlight, onClickResult, queryString, results, filterResults} = props;

  if (!results.length && !filterResults.length && queryString) {
    return <NoResults>No results</NoResults>;
  }

  return (
    <List hasResults={!!results.length || !!filterResults.length}>
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
      ) : (
        <></>
      )}
    </List>
  );
};

const NoResults = styled.div`
  color: ${Colors.textLighter()};
  font-size: 16px;
  padding: 16px;
`;

interface ListProps {
  hasResults: boolean;
}

const List = styled.ul<ListProps>`
  max-height: calc(60vh - 48px);
  margin: 0;
  padding: ${({hasResults}) => (hasResults ? '4px 0' : 'none')};
  list-style: none;
  overflow-y: auto;
  background-color: ${Colors.backgroundDefault()};
  box-shadow: 2px 2px 8px ${Colors.shadowDefault()};
  border-radius: 4px;
`;

interface HighlightableTextProps {
  readonly isHighlight: boolean;
}

const MatchingFiltersHeader = styled.li`
  background-color: ${Colors.backgroundDefault()};
  padding: 8px 12px;
  border-bottom: 1px solid ${Colors.backgroundGray()};
  color: ${Colors.textLight()};
  font-weight: 500;
`;

const Item = styled.li<HighlightableTextProps>`
  align-items: center;
  background-color: ${({isHighlight}) =>
    isHighlight ? Colors.backgroundLight() : Colors.backgroundDefault()};
  box-shadow: ${({isHighlight}) => (isHighlight ? Colors.accentLime() : 'transparent')} 4px 0 0
    inset;
  color: ${Colors.textLight()};
  display: flex;
  flex-direction: row;
  list-style: none;
  margin: 0;
  user-select: none;

  &:hover {
    background-color: ${Colors.backgroundLight()};
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
