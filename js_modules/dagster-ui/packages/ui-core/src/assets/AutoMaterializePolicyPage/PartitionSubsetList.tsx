import {
  Box,
  Colors,
  Menu,
  MenuItem,
  MiddleTruncate,
  SpinnerWithText,
  TextInput,
  TextInputContainer,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef, useState} from 'react';
import styled from 'styled-components';

import {PARTITION_SUBSET_LIST_QUERY} from './PartitionSubsetListQuery';
import {PolicyEvaluationStatusTag} from './PolicyEvaluationStatusTag';
import {AssetConditionEvaluationStatus} from './types';
import {
  PartitionSubsetListQuery,
  PartitionSubsetListQueryVariables,
} from './types/PartitionSubsetListQuery.types';
import {useQuery} from '../../apollo-client';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';

interface Props {
  description: string;
  status?: AssetConditionEvaluationStatus;
  assetKeyPath: string[];
  evaluationId: string;
  nodeUniqueId: string;
  selectPartition?: (partitionKey: string | null) => void;
}

const ITEM_HEIGHT = 32;
const MAX_ITEMS_BEFORE_TRUNCATION = 4;

export const PartitionSubsetList = ({
  description,
  status,
  assetKeyPath,
  evaluationId,
  nodeUniqueId,
  selectPartition,
}: Props) => {
  const container = useRef<HTMLDivElement | null>(null);
  const [searchValue, setSearchValue] = useState('');

  const {color, hoverColor} = useMemo(
    () => statusToColors[status ?? AssetConditionEvaluationStatus.TRUE],
    [status],
  );

  const {data, loading} = useQuery<PartitionSubsetListQuery, PartitionSubsetListQueryVariables>(
    PARTITION_SUBSET_LIST_QUERY,
    {
      variables: {
        assetKey: {path: assetKeyPath},
        evaluationId,
        nodeUniqueId,
      },
      fetchPolicy: 'cache-first',
    },
  );

  const partitionKeys = useMemo(() => {
    return data?.truePartitionsForAutomationConditionEvaluationNode || [];
  }, [data]);

  const filteredKeys = useMemo(() => {
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

  const content = () => {
    if (loading && !data) {
      return (
        <Box padding={24} flex={{direction: 'row', justifyContent: 'center'}}>
          <SpinnerWithText label="Loading partition keys…" />
        </Box>
      );
    }

    return (
      <>
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
                          if (selectPartition) {
                            selectPartition(partitionKey);
                          }
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
      </>
    );
  };

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
        {status ? <PolicyEvaluationStatusTag status={status} /> : null}
      </Box>
      {content()}
    </div>
  );
};

type ColorConfig = {
  color: string;
  hoverColor: string;
};

const statusToColors: Record<AssetConditionEvaluationStatus, ColorConfig> = {
  [AssetConditionEvaluationStatus.TRUE]: {
    color: Colors.accentGreen(),
    hoverColor: Colors.accentGreenHover(),
  },
  [AssetConditionEvaluationStatus.FALSE]: {
    color: Colors.accentYellow(),
    hoverColor: Colors.accentYellowHover(),
  },
  [AssetConditionEvaluationStatus.SKIPPED]: {
    color: Colors.accentGray(),
    hoverColor: Colors.accentGrayHover(),
  },
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
