import {
  Box,
  Menu,
  MenuItem,
  MiddleTruncate,
  Popover,
  Tag,
  TextInput,
  TextInputContainer,
  colorAccentGray,
  colorAccentGrayHover,
  colorAccentGreen,
  colorAccentGreenHover,
  colorAccentYellow,
  colorAccentYellowHover,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components';

import {assertUnreachable} from '../../app/Util';
import {AssetConditionEvaluationStatus, AssetSubsetValue} from '../../graphql/types';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {numberFormatter} from '../../ui/formatters';

import {PolicyEvaluationStatusTag} from './PolicyEvaluationStatusTag';

const statusToColors = (status: AssetConditionEvaluationStatus) => {
  switch (status) {
    case AssetConditionEvaluationStatus.TRUE:
      return {color: colorAccentGreen(), hoverColor: colorAccentGreenHover()};
    case AssetConditionEvaluationStatus.FALSE:
      return {color: colorAccentYellow(), hoverColor: colorAccentYellowHover()};
    case AssetConditionEvaluationStatus.SKIPPED:
      return {color: colorAccentGray(), hoverColor: colorAccentGrayHover()};
    default:
      return assertUnreachable(status);
  }
};

type AssetSusbsetWithoutTypenames = {
  subsetValue: Omit<AssetSubsetValue, '__typename' | 'boolValue'>;
};

interface Props {
  description: string;
  status: AssetConditionEvaluationStatus;
  subset: AssetSusbsetWithoutTypenames | null;
  selectPartition: (partitionKey: string | null) => void;
}
export const PartitionSegmentWithPopover = ({
  description,
  selectPartition,
  status,
  subset,
}: Props) => {
  const intent = React.useMemo(() => {
    switch (status) {
      case AssetConditionEvaluationStatus.FALSE:
        return 'warning' as const;
      case AssetConditionEvaluationStatus.SKIPPED:
        return undefined;
      case AssetConditionEvaluationStatus.TRUE:
        return 'success' as const;
    }
  }, [status]);

  if (!subset) {
    return null;
  }

  const count = subset.subsetValue.partitionKeys?.length || 0;

  return (
    <Popover
      interactionKind="hover"
      placement="bottom"
      hoverOpenDelay={50}
      hoverCloseDelay={50}
      content={
        <PartitionSubsetList
          description={description}
          status={status}
          subset={subset}
          selectPartition={selectPartition}
        />
      }
    >
      <Tag intent={intent}>
        {numberFormatter.format(count)} {status.charAt(0) + status.toLowerCase().slice(1)}
      </Tag>
    </Popover>
  );
};

interface ListProps {
  description: string;
  status: AssetConditionEvaluationStatus;
  subset: AssetSusbsetWithoutTypenames;
  selectPartition: (partitionKey: string | null) => void;
}

const ITEM_HEIGHT = 32;
const MAX_ITEMS_BEFORE_TRUNCATION = 4;

const PartitionSubsetList = ({description, status, subset, selectPartition}: ListProps) => {
  const container = React.useRef<HTMLDivElement | null>(null);
  const [searchValue, setSearchValue] = React.useState('');

  const {color, hoverColor} = React.useMemo(() => statusToColors(status), [status]);

  const partitionKeys = React.useMemo(() => subset.subsetValue.partitionKeys || [], [subset]);

  const filteredKeys = React.useMemo(() => {
    const searchLower = searchValue.toLocaleLowerCase();
    return partitionKeys.filter((key) => key.toLocaleLowerCase().includes(searchLower));
  }, [partitionKeys, searchValue]);

  const count = filteredKeys.length;

  const rowVirtualizer = useVirtualizer({
    count: filteredKeys.length,
    getScrollElement: () => container.current,
    estimateSize: () => ITEM_HEIGHT,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const virtualItems = rowVirtualizer.getVirtualItems();

  return (
    <div style={{width: '292px'}}>
      <Box
        padding={{vertical: 8, left: 12, right: 8}}
        border="bottom"
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        style={{display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) auto', gap: 8}}
      >
        <strong>
          <MiddleTruncate text={description} />
        </strong>
        <PolicyEvaluationStatusTag status={status} />
      </Box>
      {partitionKeys.length > MAX_ITEMS_BEFORE_TRUNCATION ? (
        <SearchContainer padding={{vertical: 4, horizontal: 8}}>
          <TextInput
            icon="search"
            placeholder="Filter partitions…"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
        </SearchContainer>
      ) : null}
      <div
        style={{
          height: count > MAX_ITEMS_BEFORE_TRUNCATION ? '150px' : count * ITEM_HEIGHT + 16,
          overflow: 'hidden',
        }}
      >
        <Container ref={container}>
          <Menu>
            <Inner $totalHeight={totalHeight}>
              {virtualItems.map(({index, key, size, start}) => {
                const partitionKey = filteredKeys[index]!;
                return (
                  <Row $height={size} $start={start} key={key}>
                    <MenuItem
                      onClick={() => {
                        selectPartition(partitionKey);
                      }}
                      text={
                        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                          <PartitionStatusDot $color={color} $hoverColor={hoverColor} />
                          <div>
                            <MiddleTruncate text={partitionKey} />
                          </div>
                        </Box>
                      }
                    />
                  </Row>
                );
              })}
            </Inner>
          </Menu>
        </Container>
      </div>
    </div>
  );
};

const SearchContainer = styled(Box)`
  display: flex;
  ${TextInputContainer} {
    flex: 1;
  }
`;

const PartitionStatusDot = styled.div<{$color: string; $hoverColor: string}>`
  background-color: ${({$color}) => $color};
  height: 8px;
  width: 8px;
  border-radius: 50%;
  transition: background-color 100ms linear;

  :hover {
    background-color: ${({$hoverColor}) => $hoverColor};
  }
`;
