import Fuse from 'fuse.js';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {ColorsWIP} from '../ui/Colors';
import {IconName, IconWIP} from '../ui/Icon';

import {SearchResult, SearchResultType} from './types';

const iconForType = (type: SearchResultType, flagPipelineModeTuples: boolean): IconName => {
  switch (type) {
    case SearchResultType.Asset:
      return 'table_view';
    case SearchResultType.PartitionSet:
    case SearchResultType.Schedule:
      return 'schedule';
    case SearchResultType.Pipeline:
      return flagPipelineModeTuples ? 'workspaces' : 'schema';
    case SearchResultType.Repository:
      return 'source';
    case SearchResultType.Run:
      return 'history';
    case SearchResultType.Sensor:
      return 'sensors';
    case SearchResultType.Solid:
      return 'linear_scale';
    default:
      return 'source';
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
        <IconWIP
          name={iconForType(item.type, flagPipelineModeTuples)}
          color={isHighlight ? ColorsWIP.White : ColorsWIP.Gray500}
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
  color: ${ColorsWIP.Gray100};
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
  background-color: ${({isHighlight}) => (isHighlight ? ColorsWIP.Blue500 : ColorsWIP.White)};
  color: ${({isHighlight}) => (isHighlight ? ColorsWIP.White : 'default')}
  display: flex;
  flex-direction: row;
  list-style: none;
  margin: 0;
  user-select: none;

  &:hover {
    background-color: ${({isHighlight}) => (isHighlight ? ColorsWIP.Blue500 : ColorsWIP.Gray500)};
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
  color: ${({isHighlight}) => (isHighlight ? ColorsWIP.White : ColorsWIP.Gray500)};
  font-weight: 500;
`;

const Description = styled.div<HighlightableTextProps>`
  color: ${({isHighlight}) => (isHighlight ? ColorsWIP.White : ColorsWIP.Gray400)};
  font-size: 12px;
  max-width: 530px;
  overflow-x: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;
