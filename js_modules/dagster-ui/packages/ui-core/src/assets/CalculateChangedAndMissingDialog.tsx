import {gql, useQuery} from '@apollo/client';
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
import {
  AssetStaleStatusQuery,
  AssetStaleStatusQueryVariables,
} from './types/CalculateChangedAndMissingDialog.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

export const CalculateChangedAndMissingDialog = React.memo(
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

    const staleOrMissing = React.useMemo(
      () =>
        data?.assetNodes
          .filter((node) => isAssetStale(node.assetKey, node, 'all') || isAssetMissing(node))
          .map(asAssetKeyInput),
      [data],
    );

    React.useEffect(() => {
      if (isOpen && !loading && (!data || error)) {
        showCustomAlert({
          title: 'Could not fetch stale status for assets',
          body: 'An unknown error occurred.',
        });
        onClose();
      }
    }, [data, error, isOpen, loading, onClose]);

    const containerRef = React.useRef<HTMLDivElement | null>(null);
    const virtualizer = useVirtualizer({
      count: staleOrMissing?.length ?? 0,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 28,
    });
    const totalHeight = virtualizer.getTotalSize();
    const items = virtualizer.getVirtualItems();

    const [checked, setChecked] = React.useState<Set<AssetKey>>(new Set());
    React.useLayoutEffect(() => {
      setChecked(new Set(staleOrMissing));
    }, [staleOrMissing]);

    const content = () => {
      if (!isOpen) {
        return null;
      }
      if (loading) {
        return (
          <Box flex={{alignItems: 'center', gap: 8}}>
            <Spinner purpose="body-text" /> Fetching asset statuses
          </Box>
        );
      }
      if (staleOrMissing?.length) {
        return (
          <>
            <RowGrid border="bottom" padding={{bottom: 8}}>
              <Checkbox
                id="check-all"
                checked={checked.size === staleOrMissing.length}
                onChange={() => {
                  setChecked((checked) => {
                    if (checked.size === staleOrMissing.length) {
                      return new Set();
                    } else {
                      return new Set(staleOrMissing);
                    }
                  });
                }}
              />
              <label htmlFor="check-all" style={{color: Colors.textLight(), cursor: 'pointer'}}>
                Asset Name
              </label>
            </RowGrid>
            <Container ref={containerRef} style={{maxHeight: '400px'}}>
              <Inner $totalHeight={totalHeight}>
                {items.map(({index, key, size, start}) => {
                  const item = staleOrMissing[index]!;
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
                        <Box
                          as="label"
                          htmlFor={`checkbox-${key}`}
                          flex={{alignItems: 'center', gap: 4}}
                          style={{cursor: 'pointer'}}
                        >
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
          <div>All assets are up to date</div>
        </Box>
      );
    };
    return (
      <>
        <Dialog isOpen={isOpen} onClose={onClose} title="Materialize unsynced assets">
          <DialogBody>{content()}</DialogBody>
          <DialogFooter topBorder>
            {loading ? (
              <Button onClick={onClose}>Cancel</Button>
            ) : staleOrMissing?.length ? (
              <Button
                intent="primary"
                onClick={(e) => {
                  onMaterializeAssets(Array.from(checked), e);
                  onClose();
                }}
                disabled={checked.size === 0}
              >
                Materialize {checked.size} assets
              </Button>
            ) : (
              <Button onClick={onClose}>Dismiss</Button>
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
      staleStatus
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
