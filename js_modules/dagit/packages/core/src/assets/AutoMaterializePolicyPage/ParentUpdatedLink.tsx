import {
  ButtonLink,
  Box,
  Colors,
  TextInput,
  Dialog,
  DialogFooter,
  Button,
  NonIdealState,
} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {AssetLink} from '../AssetLink';
import {AssetKey} from '../types';

type AssetKeyDetail = {assetKey: AssetKey; detailType: string};

interface Props {
  updatedAssetKeys: AssetKey[];
  willUpdateAssetKeys: AssetKey[];
}

export const ParentUpdatedLink = ({updatedAssetKeys, willUpdateAssetKeys}: Props) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [queryString, setQueryString] = React.useState('');
  const queryLowercase = queryString.toLocaleLowerCase();

  const allAssetKeyDetails: AssetKeyDetail[] = React.useMemo(() => {
    return [
      ...updatedAssetKeys.map((assetKey) => ({assetKey, detailType: '(Updated)'})),
      ...willUpdateAssetKeys.map((assetKey) => ({assetKey, detailType: '(Will update)'})),
    ];
  }, [updatedAssetKeys, willUpdateAssetKeys]);

  const count = allAssetKeyDetails.length;

  const filteredAssetKeys = React.useMemo(() => {
    if (queryLowercase === '') {
      return allAssetKeyDetails;
    }
    return allAssetKeyDetails.filter((assetKeyDetail) =>
      assetKeyDetail.assetKey.path.some((part) => part.toLowerCase().includes(queryLowercase)),
    );
  }, [allAssetKeyDetails, queryLowercase]);

  const label = React.useMemo(
    () => (count === 1 ? '1 parent updated' : `${count} parents updated`),
    [count],
  );

  const content = () => {
    if (queryString && !filteredAssetKeys.length) {
      return (
        <Box padding={32}>
          <NonIdealState
            icon="search"
            title="No matching asset keys"
            description={
              <>
                No matching asset keys for <strong>{queryString}</strong>
              </>
            }
          />
        </Box>
      );
    }

    return <VirtualizedWaitingOnAssetList assetKeyDetails={filteredAssetKeys} />;
  };

  return (
    <>
      <ButtonLink onClick={() => setIsOpen(true)}>{label}</ButtonLink>
      <Dialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        style={{width: '750px', maxWidth: '80vw', minWidth: '500px'}}
        canOutsideClickClose
        canEscapeKeyClose
      >
        <Box
          padding={{horizontal: 24, vertical: 16}}
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <div style={{fontSize: '16px'}}>{count === 1 ? '1 asset' : `${count} assets`}</div>
          {count > 0 ? (
            <TextInput
              icon="search"
              value={queryString}
              onChange={(e) => setQueryString(e.target.value)}
              placeholder="Filter by asset key…"
              style={{width: '252px'}}
            />
          ) : null}
        </Box>
        <div style={{height: '272px', overflow: 'hidden'}}>{content()}</div>
        <DialogFooter topBorder>
          <Button onClick={() => setIsOpen(false)}>Close</Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

interface VirtualizedWaitingOnAssetListProps {
  assetKeyDetails: AssetKeyDetail[];
}

const VirtualizedWaitingOnAssetList = ({assetKeyDetails}: VirtualizedWaitingOnAssetListProps) => {
  const container = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: assetKeyDetails.length,
    getScrollElement: () => container.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <Container ref={container} style={{padding: '8px 24px'}}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const assetKeyDetail = assetKeyDetails[index]!;
          return (
            <Row $height={size} $start={start} key={key}>
              <Box
                style={{height: '100%'}}
                flex={{direction: 'row', alignItems: 'center'}}
                border={
                  index < assetKeyDetails.length - 1
                    ? {side: 'bottom', width: 1, color: Colors.KeylineGray}
                    : null
                }
              >
                <AssetLink path={assetKeyDetail.assetKey.path} icon="asset" />
                &nbsp;{assetKeyDetail.detailType}
              </Box>
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};
