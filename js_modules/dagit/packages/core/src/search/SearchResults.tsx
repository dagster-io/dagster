import {Colors, Icon, IconName} from '@blueprintjs/core';
import Fuse from 'fuse.js';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';

import {SearchResult, SearchResultType} from './types';

export const iconForType = (type: SearchResultType, flagPipelineModeTuples: boolean): IconName => {
  switch (type) {
    case SearchResultType.Asset:
      return 'th';
    case SearchResultType.PartitionSet:
      return 'time';
    case SearchResultType.Pipeline:
      return flagPipelineModeTuples ? 'send-to-graph' : 'diagram-tree';
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
  isHighlight: boolean;
  onClickResult: (result: Fuse.FuseResult<SearchResult>) => void;
  result: Fuse.FuseResult<SearchResult>;
}

const SearchResultItem: React.FC<ItemProps> = React.memo(({isHighlight, onClickResult, result}) => {
  const {item} = result;
  const element = React.useRef<HTMLLIElement>(null);
  const {flagPipelineModeTuples} = useFeatureFlags();

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
      <ResultLink to={item.href} onClick={onClick}>
        <Icon
          iconSize={16}
          icon={iconForType(item.type, flagPipelineModeTuples)}
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
  onClickResult: (result: Fuse.FuseResult<SearchResult>) => void;
  queryString: string;
  results: Fuse.FuseResult<SearchResult>[];
  style?: React.CSSProperties;
}

export const SearchResults = (props: Props) => {
  const {highlight, onClickResult, queryString, results, style} = props;

  if (!results.length && queryString) {
    return <NoResults style={style}>No results</NoResults>;
  }

  return (
    <List hasResults={!!results.length} style={style}>
      {results.map((result, ii) => (
        <SearchResultItem
          key={result.item.key}
          isHighlight={highlight === ii}
          result={result}
          onClickResult={onClickResult}
        />
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
  user-select: none;

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
  max-width: 530px;
  overflow-x: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;
