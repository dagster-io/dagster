import {
  Box,
  MiddleTruncate,
  Popover,
  TextInput,
  TextInputContainer,
  Colors,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components';

import {assertUnreachable} from '../../app/Util';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';

import {PolicyEvaluationStatusTag} from './PolicyEvaluationStatusTag';
import {AssetConditionEvaluationStatus, AssetSubset} from './types';

const statusToColors = (status: AssetConditionEvaluationStatus) => {
  switch (status) {
    case AssetConditionEvaluationStatus.TRUE:
      return {color: Colors.accentGreen(), hoverColor: Colors.accentGreenHover()};
    case AssetConditionEvaluationStatus.FALSE:
      return {color: Colors.accentYellow(), hoverColor: Colors.accentYellowHover()};
    case AssetConditionEvaluationStatus.SKIPPED:
      return {color: Colors.accentGray(), hoverColor: Colors.accentGrayHover()};
    default:
      return assertUnreachable(status);
  }
};

interface Props {
  description: string;
  status: AssetConditionEvaluationStatus;
  subset: AssetSubset | null;
  width: number;
}

export const PartitionSegmentWithPopover = ({description, width, status, subset}: Props) => {
  const {color, hoverColor} = React.useMemo(() => statusToColors(status), [status]);
  const segment = <PartitionSegment $color={color} $hoverColor={hoverColor} $width={width} />;
  if (!subset) {
    return segment;
  }

  return (
    <SegmentContainer $width={width}>
      <Popover
        interactionKind="hover"
        placement="bottom"
        hoverOpenDelay={50}
        hoverCloseDelay={50}
        content={<PartitionSubsetList description={description} status={status} subset={subset} />}
      >
        {segment}
      </Popover>
    </SegmentContainer>
  );
};

interface ListProps {
  description: string;
  status: AssetConditionEvaluationStatus;
  subset: AssetSubset;
}

const ITEM_HEIGHT = 32;
const MAX_ITEMS_BEFORE_TRUNCATION = 4;

const PartitionSubsetList = ({description, status, subset}: ListProps) => {
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
          height: count > MAX_ITEMS_BEFORE_TRUNCATION ? '150px' : count * ITEM_HEIGHT,
          overflow: 'hidden',
        }}
      >
        <Container ref={container}>
          <Inner $totalHeight={totalHeight}>
            {virtualItems.map(({index, key, size, start}) => {
              const partitionKey = filteredKeys[index]!;
              return (
                <Row $height={size} $start={start} key={key}>
                  <Box
                    style={{height: '100%'}}
                    padding={{vertical: 8, horizontal: 16}}
                    flex={{direction: 'row', alignItems: 'center', gap: 8}}
                  >
                    <PartitionStatusDot $color={color} $hoverColor={hoverColor} />
                    <div>
                      <MiddleTruncate text={partitionKey} />
                    </div>
                  </Box>
                </Row>
              );
            })}
          </Inner>
        </Container>
      </div>
    </div>
  );
};

const SegmentContainer = styled.div.attrs<{$width: number}>(({$width}) => ({
  style: {
    flexBasis: `${$width}px`,
  },
}))<{$width: number}>`
  .bp4-popover2-target {
    display: block;
  }
`;

const SearchContainer = styled(Box)`
  display: flex;
  ${TextInputContainer} {
    flex: 1;
  }
`;

interface PartitionSegmentProps {
  $color: string;
  $hoverColor: string;
  $width: number;
}

const PartitionSegment = styled.div.attrs<PartitionSegmentProps>(({$width}) => ({
  style: {
    flexBasis: `${$width}px`,
  },
}))<PartitionSegmentProps>`
  background-color: ${({$color}) => $color};
  border-radius: 2px;
  height: 20px;
  transition: background-color 100ms linear;

  :hover {
    background-color: ${({$hoverColor}) => $hoverColor};
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
