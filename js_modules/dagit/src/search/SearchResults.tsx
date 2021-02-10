import {Colors, Icon, IconName} from '@blueprintjs/core';
import Fuse from 'fuse.js';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {SearchResult, SearchResultType} from 'src/search/types';

const iconForType = (type: SearchResultType): IconName => {
  switch (type) {
    case SearchResultType.Asset:
      return 'th';
    case SearchResultType.Pipeline:
      return 'diagram-tree';
    case SearchResultType.Repository:
      return 'folder-open';
    case SearchResultType.Run:
      return 'history';
    case SearchResultType.Schedule:
      return 'time';
    case SearchResultType.Sensor:
      return 'automatic-updates';
    case SearchResultType.Solid:
      return 'git-commit';
    default:
      return 'cube';
  }
};

interface ItemProps {
  result: Fuse.FuseResult<SearchResult>;
  isHighlight: boolean;
}

const SearchResultItem: React.FC<ItemProps> = React.memo(({result, isHighlight}) => {
  const {item} = result;
  const element = React.useRef<HTMLLIElement>(null);

  React.useEffect(() => {
    if (element.current && isHighlight) {
      element.current.scrollIntoView({block: 'nearest'});
    }
  }, [isHighlight]);

  return (
    <Item isHighlight={isHighlight} ref={element}>
      <ResultLink to={item.href}>
        <Icon
          iconSize={16}
          icon={iconForType(item.type)}
          color={isHighlight ? Colors.WHITE : Colors.GRAY3}
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
  queryString: string;
  results: Fuse.FuseResult<SearchResult>[];
}

export const SearchResults = (props: Props) => {
  const {highlight, queryString, results} = props;

  if (!results.length && queryString) {
    return <NoResults>No results</NoResults>;
  }

  return (
    <List hasResults={!!results.length}>
      {results.map((result, ii) => (
        <SearchResultItem key={result.item.key} isHighlight={highlight === ii} result={result} />
      ))}
    </List>
  );
};

const NoResults = styled.div`
  color: ${Colors.GRAY5};
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
  background-color: ${({isHighlight}) => (isHighlight ? Colors.BLUE3 : Colors.WHITE)};
  color: ${({isHighlight}) => (isHighlight ? Colors.WHITE : 'default')}
  display: flex;
  flex-direction: row;
  list-style: none;
  margin: 0;

  &:hover {
    background-color: ${({isHighlight}) => (isHighlight ? Colors.BLUE3 : Colors.LIGHT_GRAY3)};
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
  color: ${({isHighlight}) => (isHighlight ? Colors.WHITE : Colors.GRAY1)};
  font-weight: 500;
`;

const Description = styled.div<HighlightableTextProps>`
  color: ${({isHighlight}) => (isHighlight ? Colors.WHITE : Colors.GRAY3)};
  font-size: 12px;
`;
