import {
  Box,
  Colors,
  Icon,
  MiddleTruncate,
  Popover,
  Tag,
  ToggleButton,
} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {AssetTimelineRowDataState, DataFetcherContext} from './AssetTimelineDataFetcher';
import {NodeType} from './OverviewAssetsRoot';
import {RunWithAssetsFragment} from './types/AssetTimelineDataFetcher.types';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {SidebarItemContainer, SidebarItemWrapper} from '../../asset-graph/sidebar/AssetSidebarNode';
import {failedStatuses} from '../../runs/RunStatuses';
import {
  BatchCount,
  MIN_CHUNK_WIDTH,
  MIN_WIDTH_FOR_MULTIPLE,
  RunChunk,
  RunChunks,
  RunHoverContent,
} from '../../runs/RunTimeline';
import {batchRunsForTimeline} from '../../runs/batchRunsForTimeline';
import {mergeStatusToBackground} from '../../runs/mergeStatusToBackground';
import {Row, RowCell} from '../../ui/VirtualizedTable';
import {numberFormatter} from '../../ui/formatters';

type RowProps = {
  sidebarWidth: number;
  node: NodeType;
  top: number;
  height: number;
  range: [number, number];
  timelineWidth: number;
  openNodes: Set<string>;
  setOpenNodes: (setter: React.SetStateAction<Set<string> | undefined>) => void;
};
export function AssetTimelineRow({
  height,
  top,
  range,
  sidebarWidth,
  node,
  timelineWidth,
  openNodes,
  setOpenNodes,
}: RowProps) {
  const [start, end] = range;
  const dataContext = React.useContext(DataFetcherContext);
  const [data, setData] = React.useState<AssetTimelineRowDataState>({runs: [], loading: true});
  React.useEffect(() => {
    if (node.type === 'location') {
      const unsubscribe = dataContext.subscribeToCodeLocationData(node.id, setData);
      return unsubscribe;
    } else if (node.type === 'asset') {
      const unsubscribe = dataContext.subscribeToAssetData(node.asset.key, setData);
      return unsubscribe;
    } else {
      const unsubscribe = dataContext.subscribeToGroupData(node.id, setData);
      return unsubscribe;
    }
  }, [dataContext, node, setData]);

  const batched = React.useMemo(() => {
    return batchRunsForTimeline<RunWithAssetsFragment & {startTime: number}>({
      runs: data.runs.filter(
        (run) => run.startTime !== null && (!run.endTime || run.endTime > start / 1000),
        // as any because typescript doesn't seem to refine my type as having a non-nullable startTime
        // even though I checked for that above
      ) as any,
      start: start / 1000,
      end: end / 1000,
      width: timelineWidth,
      minChunkWidth: MIN_CHUNK_WIDTH,
      minMultipleWidth: MIN_WIDTH_FOR_MULTIPLE,
    });
  }, [data, end, start, timelineWidth]);

  const name = React.useMemo(() => {
    if (node.type === 'location') {
      return node.locationName;
    } else if (node.type === 'asset') {
      return tokenForAssetKey(node.asset.key);
    } else {
      return node.groupName;
    }
  }, [node]);

  const isOpen = openNodes.has(node.id);
  const icon = React.useMemo(() => {
    if (node.type === 'asset') {
      return null;
    } else if (node.type === 'location') {
      return <Icon name="folder_open" color={isOpen ? Colors.textDisabled() : undefined} />;
    } else {
      return <Icon name="asset_group" color={isOpen ? Colors.textDisabled() : undefined} />;
    }
  }, [node, isOpen]);

  const failureCount = React.useMemo(() => {
    return batched.reduce((prev, batch) => {
      if (failedStatuses.has(batch.runs[0]?.status as any)) {
        return prev + batch.runs.length;
      }
      return prev;
    }, 0);
  }, [batched]);

  return (
    <Row $height={height} $start={top}>
      <RowGrid $sidebarWidth={sidebarWidth}>
        <Cell border="right" padding={undefined}>
          <ItemWrapper2 isOpen={openNodes.has(node.id)}>
            <SidebarItemWrapper level={node.level}>
              <SidebarItemContainer
                onClick={() => {
                  if (node.type === 'asset') {
                    return;
                  }
                  setOpenNodes((nodes) => {
                    const copy = new Set(nodes);
                    if (copy.has(node.id)) {
                      copy.delete(node.id);
                    } else {
                      copy.add(node.id);
                    }
                    return copy;
                  });
                }}
              >
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: node.type !== 'asset' ? 'auto 1fr' : '1fr',
                    alignItems: 'center',
                    width: '100%',
                  }}
                >
                  {node.type !== 'asset' ? (
                    <ToggleButton onToggle={() => {}} isOpen={openNodes.has(node.id)} />
                  ) : null}
                  <div
                    style={{
                      display: 'grid',
                      gap: 4,
                      gridTemplateColumns: icon ? 'auto 1fr auto' : '1fr auto',
                      gridTemplateRows: '1fr',
                      width: '100%',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    {icon}
                    <MiddleTruncate text={name} />
                    {failureCount ? (
                      <Tag intent="danger">{numberFormatter.format(failureCount)}</Tag>
                    ) : null}
                  </div>
                </div>
              </SidebarItemContainer>
            </SidebarItemWrapper>
          </ItemWrapper2>
        </Cell>
        <Cell
          border="bottom"
          padding={undefined}
          style={{background: isOpen ? Colors.backgroundLight() : undefined}}
        >
          <RunChunks height={34}>
            {batched.map((batch) => {
              const {left, width, runs} = batch;
              const runCount = runs.length;
              return (
                <RunChunk
                  key={batch.runs[0]!.id}
                  $background={
                    isOpen ? Colors.backgroundLighter() : mergeStatusToBackground(batch.runs)
                  }
                  $multiple={runCount > 1}
                  style={{
                    left: `${left}px`,
                    width: `${width}px`,
                  }}
                >
                  <Popover
                    content={
                      <RunHoverContent
                        job={{
                          jobName: name,
                          jobType: 'asset',
                          key: name,
                          path: '',
                          repoAddress: node.repoAddress,
                          runs: batch.runs,
                        }}
                        batch={batch}
                      />
                    }
                    position="top"
                    interactionKind="hover"
                    className="chunk-popover-target"
                  >
                    <Box
                      flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
                      style={{height: '100%'}}
                    >
                      {runCount > 1 ? <BatchCount>{batch.runs.length}</BatchCount> : null}
                    </Box>
                  </Popover>
                </RunChunk>
              );
            })}
          </RunChunks>
        </Cell>
      </RowGrid>
    </Row>
  );
}

const RowGrid = styled(Box)<{$sidebarWidth: number}>`
  display: grid;
  grid-template-columns: ${({$sidebarWidth}) => `${$sidebarWidth}px 1fr`};
  height: 100%;
  > * {
    vertical-align: middle;
  }
`;

const Cell = ({
  children,
  ...rest
}: {children: React.ReactNode} & React.ComponentProps<typeof RowCell>) => {
  return (
    <RowCell style={{color: Colors.textDefault()}} border={undefined} padding={4} {...rest}>
      {children}
    </RowCell>
  );
};

const ItemWrapper2 = styled.div<{isOpen: boolean}>`
button {
  padding-left: 0px;
  height: 34px;
}
width: 100%;
* {
  ${({isOpen}) => (isOpen ? `* { color: ${Colors.textDisabled()} }` : undefined)}
`;
