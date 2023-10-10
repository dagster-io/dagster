import {useQuery, gql} from '@apollo/client';
import {
  Spinner,
  Dialog,
  DialogBody,
  DialogFooter,
  Button,
  Box,
  Icon,
  Colors,
  Checkbox,
  MiddleTruncate,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

import {useMaterializationAction} from './LaunchAssetExecutionButton';
import {isAssetStale, isAssetMissing} from './Stale';
import {asAssetKeyInput} from './asInput';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey} from './types';
import {
  AssetStaleStatusQuery,
  AssetStaleStatusQueryVariables,
} from './types/CalculateChangedAndMissingDialog.types';

export const CalculateChangedAndMissingDialog = React.memo(
  ({
    isOpen,
    onClose,
    assets,
    preferredJobName,
  }: {
    isOpen: boolean;
    assets: {
      assetKey: AssetKey;
    }[];
    onClose: () => void;
    preferredJobName?: string;
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
    const {
      onClick,
      loading: materializeActionLoading,
      launchpadElement,
    } = useMaterializationAction(preferredJobName);

    const staleOrMissing = React.useMemo(
      () =>
        data?.assetNodes
          .filter((node) => isAssetStale(node) || isAssetMissing(node))
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
      if (loading || materializeActionLoading) {
        return (
          <Box flex={{alignItems: 'center', gap: 8}}>
            <Spinner purpose="body-text" /> Fetching asset statuses
          </Box>
        );
      }
      if (staleOrMissing?.length) {
        return (
          <Container ref={containerRef} style={{maxHeight: '500px'}}>
            <Inner $totalHeight={totalHeight}>
              {items.map(({index, key, size, start, measureElement}) => {
                const item = staleOrMissing[index]!;
                return (
                  <Row $height={size} $start={start} key={key} ref={measureElement}>
                    <RowGrid border="bottom">
                      <Checkbox
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
                      <Link to={assetDetailsPathForKey(item)}>
                        <MiddleTruncate text={displayNameForAssetKey(item)} />
                      </Link>
                    </RowGrid>
                  </Row>
                );
              })}
            </Inner>
          </Container>
        );
      }
      return (
        <Box flex={{alignItems: 'center', gap: 8}}>
          <Icon name="check_circle" color={Colors.Green500} />
          <div>All assets are up to date</div>
        </Box>
      );
    };
    return (
      <>
        {launchpadElement}
        <Dialog isOpen={isOpen} onClose={onClose} title="Materialize changed and missing assets">
          <DialogBody>{content()}</DialogBody>
          <DialogFooter topBorder>
            {loading ? (
              <Button onClick={onClose}>Cancel</Button>
            ) : staleOrMissing?.length ? (
              <Button
                intent="primary"
                onClick={(e) => {
                  onClick(Array.from(checked), e);
                  onClose();
                }}
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
