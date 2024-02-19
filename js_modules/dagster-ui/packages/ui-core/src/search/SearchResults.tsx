import {Colors, Icon, IconName} from '@dagster-io/ui-components';
import Fuse from 'fuse.js';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {SearchResult, SearchResultType} from './types';

const iconForType = (type: SearchResultType): IconName => {
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
    default:
      return 'source';
  }
};

interface ItemProps {
  isHighlight: boolean;
  onClickResult: (result: Fuse.FuseResult<SearchResult>) => void;
  result: Fuse.FuseResult<SearchResult>;
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

  return (
    <Item isHighlight={isHighlight} ref={element}>
      <ResultLink to={item.href} onMouseDown={onClick}>
        <Icon
          name={iconForType(item.type)}
          color={isHighlight ? Colors.textDefault() : Colors.textLight()}
        />
        <div style={{marginLeft: '12px'}}>
          <Label isHighlight={isHighlight}>{item.label}</Label>
          <Description isHighlight={isHighlight}>{item.description}</Description>
        </div>
      </ResultLink>
    </Item>
  );
});

interface Props {
  highlight: number;
  onClickResult: (result: Fuse.FuseResult<SearchResult>) => void;
  queryString: string;
  results: Fuse.FuseResult<SearchResult>[];
}

export const SearchResults = (props: Props) => {
  const {highlight, onClickResult, queryString, results} = props;

  if (!results.length && queryString) {
    return <NoResults>No results</NoResults>;
  }

  return (
    <List hasResults={!!results.length}>
      {results.map((result, ii) => (
        <SearchResultItem
          key={result.item.href}
          isHighlight={highlight === ii}
          result={result}
          onClickResult={onClickResult}
        />
      ))}
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
`;

interface HighlightableTextProps {
  readonly isHighlight: boolean;
}

const Item = styled.li<HighlightableTextProps>`
  align-items: center;
  background-color: ${({isHighlight}) => (isHighlight ? Colors.backgroundLight() : 'transparent')};
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

const Label = styled.div<HighlightableTextProps>`
  color: ${({isHighlight}) => (isHighlight ? Colors.textDefault() : Colors.textLight())};
  font-weight: 500;
`;

const Description = styled.div<HighlightableTextProps>`
  color: ${({isHighlight}) => (isHighlight ? Colors.textDefault() : Colors.textLight())};
  font-size: 12px;
  max-width: 530px;
  overflow-x: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;
