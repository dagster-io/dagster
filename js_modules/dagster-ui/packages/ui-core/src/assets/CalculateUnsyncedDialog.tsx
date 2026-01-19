import {
  Box,
  Button,
  Checkbox,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  MiddleTruncate,
  Spinner,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {isAssetMissing, isAssetStale} from './Stale';
import {asAssetKeyInput} from './asInput';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey} from './types';
import {gql, useQuery} from '../apollo-client';
import {
  AssetStaleStatusQuery,
  AssetStaleStatusQueryVariables,
} from './types/CalculateUnsyncedDialog.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

export const CalculateUnsyncedDialog = React.memo(
  ({
    isOpen,
    onClose,
    assets,
    onMaterializeAssets,
  }: {
    isOpen: boolean;
    assets: {
      assetKey: AssetKey;
    }[];
    onClose: () => void;
    onMaterializeAssets: (assets: AssetKey[], e: React.MouseEvent<any>) => void;
  }) => {
    const {data, loading, error} = useQuery<AssetStaleStatusQuery, AssetStaleStatusQueryVariables>(
      ASSET_STALE_STATUS_QUERY,
      {
        variables: {
          assetKeys: assets.map(asAssetKeyInput),
        },
        skip: !isOpen,
      },
    );

    const unsynced = React.useMemo(
      () =>
        (data?.assetNodes || [])
          .filter((node) => node.isMaterializable && (isAssetStale(node) || isAssetMissing(node)))
          .map(asAssetKeyInput),
      [data],
    );

    React.useEffect(() => {
      if (isOpen && !loading && (!data || error)) {
        showCustomAlert({
          title: '无法获取资产的过期状态',
          body: '发生未知错误。',
        });
        onClose();
      }
    }, [data, error, isOpen, loading, onClose]);

    const containerRef = React.useRef<HTMLDivElement | null>(null);
    const virtualizer = useVirtualizer({
      count: unsynced.length,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 28,
    });
    const totalHeight = virtualizer.getTotalSize();
    const items = virtualizer.getVirtualItems();

    const [checked, setChecked] = React.useState<Set<AssetKey>>(new Set());
    React.useLayoutEffect(() => {
      setChecked(new Set(unsynced));
    }, [unsynced]);

    const content = () => {
      if (!isOpen) {
        return null;
      }
      if (loading) {
        return (
          <Box flex={{alignItems: 'center', gap: 8}}>
            <Spinner purpose="body-text" /> 正在获取资产状态
          </Box>
        );
      }
      if (unsynced.length) {
        return (
          <>
            <RowGrid border="bottom" padding={{bottom: 8}}>
              <Checkbox
                id="check-all"
                checked={checked.size === unsynced.length}
                onChange={() => {
                  setChecked((checked) => {
                    if (checked.size === unsynced.length) {
                      return new Set();
                    } else {
                      return new Set(unsynced);
                    }
                  });
                }}
              />
              <label htmlFor="check-all" style={{color: Colors.textLight(), cursor: 'pointer'}}>
                资产名称
              </label>
            </RowGrid>
            <Container ref={containerRef} style={{maxHeight: '400px'}}>
              <Inner $totalHeight={totalHeight}>
                {items.map(({index, key, size, start}) => {
                  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                  const item = unsynced[index]!;
                  return (
                    <Row
                      $height={size}
                      $start={start}
                      data-key={key}
                      key={key}
                      ref={virtualizer.measureElement}
                    >
                      <RowGrid border="bottom">
                        <Checkbox
                          id={`checkbox-${key}`}
                          checked={checked.has(item)}
                          onChange={() => {
                            setChecked((checked) => {
                              const copy = new Set(checked);
                              if (copy.has(item)) {
                                copy.delete(item);
                              } else {
                                copy.add(item);
                              }
                              return copy;
                            });
                          }}
                        />
                        <Box flex={{alignItems: 'center', gap: 4}} style={{cursor: 'pointer'}}>
                          <Box style={{overflow: 'hidden'}}>
                            <MiddleTruncate text={displayNameForAssetKey(item)} />
                          </Box>
                          <Link to={assetDetailsPathForKey(item)} target="_blank">
                            <Icon name="open_in_new" color={Colors.linkDefault()} />
                          </Link>
                        </Box>
                      </RowGrid>
                    </Row>
                  );
                })}
              </Inner>
            </Container>
          </>
        );
      }
      return (
        <Box flex={{alignItems: 'center', gap: 8}}>
          <Icon name="check_circle" color={Colors.accentGreen()} />
          <div>所有资产均已更新</div>
        </Box>
      );
    };
    return (
      <>
        <Dialog isOpen={isOpen} onClose={onClose} title="物化未同步的资产">
          <DialogBody>{content()}</DialogBody>
          <DialogFooter topBorder>
            {loading ? (
              <Button onClick={onClose}>取消</Button>
            ) : unsynced.length ? (
              <Button
                intent="primary"
                onClick={(e) => {
                  onMaterializeAssets(Array.from(checked), e);
                  onClose();
                }}
                disabled={checked.size === 0}
              >
                物化 {checked.size} 个资产
              </Button>
            ) : (
              <Button onClick={onClose}>关闭</Button>
            )}
          </DialogFooter>
        </Dialog>
      </>
    );
  },
);

const ASSET_STALE_STATUS_QUERY = gql`
  query AssetStaleStatusQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      assetKey {
        path
      }
      isMaterializable
      staleStatus
      partitionStats {
        numMaterialized
        numMaterializing
        numPartitions
        numFailed
      }
    }
  }
`;

const TEMPLATE_COLUMNS = '20px minmax(0, 1fr)';

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  gap: 8px;
  height: 100%;
  align-items: center;
`;
