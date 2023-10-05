import {
  Box,
  Colors,
  Subtitle2,
  Caption,
  Tag,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  ButtonLink,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import styled from 'styled-components';

import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {formatElapsedTime} from '../../app/Util';
import {Timestamp} from '../../app/time/Timestamp';
import {PythonErrorFragment} from '../../app/types/PythonErrorFragment.types';
import {AssetKeyInput, InstigationTickStatus} from '../../graphql/types';
import {HeaderCell, Inner, Row, RowCell} from '../../ui/VirtualizedTable';
import {AssetLink} from '../AssetLink';
import {
  AssetKeysDialog,
  AssetKeysDialogHeader,
  AssetKeysDialogEmptyState,
} from '../AutoMaterializePolicyPage/AssetKeysDialog';

import {AssetDaemonTickFragment} from './types/AutomaterializationRoot.types';
const TEMPLATE_COLUMNS = '30% 17% 53%';

export const AutomaterializationTickDetailDialog = React.memo(
  ({
    tick,
    isOpen,
    close,
  }: {
    tick: AssetDaemonTickFragment | null;
    isOpen: boolean;
    close: () => void;
  }) => {
    const [queryString, setQueryString] = React.useState('');

    const filteredAssetKeys = React.useMemo(
      () =>
        tick
          ? tick.requestedAssetKeys.filter((assetKey) =>
              assetKey.path.join('/').includes(queryString),
            )
          : [],
      [tick, queryString],
    );

    const count = tick?.requestedAssetKeys.length || 0;

    const parentRef = React.useRef<HTMLDivElement | null>(null);
    const rowVirtualizer = useVirtualizer({
      count: filteredAssetKeys.length,
      getScrollElement: () => parentRef.current,
      estimateSize: () => 34,
      overscan: 10,
    });
    const totalHeight = rowVirtualizer.getTotalSize();
    const items = rowVirtualizer.getVirtualItems();

    const content = React.useMemo(() => {
      if (queryString && !filteredAssetKeys.length) {
        return (
          <AssetKeysDialogEmptyState
            title="No matching asset keys"
            description={
              <>
                No matching asset keys for <strong>{queryString}</strong>
              </>
            }
          />
        );
      }
      if (!tick?.requestedAssetKeys.length) {
        return (
          <Box padding={{vertical: 12, horizontal: 24}}>
            <Caption color={Colors.Gray700}>None</Caption>
          </Box>
        );
      }
      return (
        <div style={{overflow: 'scroll'}} ref={parentRef}>
          <Box
            border="top-and-bottom"
            style={{
              display: 'grid',
              gridTemplateColumns: TEMPLATE_COLUMNS,
              height: '32px',
              fontSize: '12px',
              color: Colors.Gray600,
              position: 'sticky',
              top: 0,
              zIndex: 1,
              background: Colors.White,
            }}
          >
            <HeaderCell>Asset</HeaderCell>
            <HeaderCell>Group</HeaderCell>
            <HeaderCell>Result</HeaderCell>
          </Box>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const assetKey = filteredAssetKeys[index]!;
              return <AssetDetailRow key={key} $height={size} $start={start} assetKey={assetKey} />;
            })}
          </Inner>
        </div>
      );
    }, [filteredAssetKeys, items, queryString, tick, totalHeight]);

    const intent = React.useMemo(() => {
      switch (tick?.status) {
        case InstigationTickStatus.FAILURE:
          return 'danger';
        case InstigationTickStatus.STARTED:
          return 'primary';
        case InstigationTickStatus.SUCCESS:
          return 'success';
      }
      return undefined;
    }, [tick]);

    const [showPythonError, setShowPythonError] = React.useState<PythonErrorFragment | null>(null);

    return (
      <AssetKeysDialog
        isOpen={isOpen}
        setIsOpen={close}
        height={400}
        header={
          <AssetKeysDialogHeader
            title={
              tick ? (
                <div>
                  <Timestamp timestamp={{unix: tick.timestamp}} dateTimeSeparator=" at " />
                </div>
              ) : (
                ''
              )
            }
            showSearch={count > 0}
            placeholder="Filter by asset key…"
            queryString={queryString}
            setQueryString={setQueryString}
          />
        }
        content={
          <div
            style={{
              display: 'grid',
              gridTemplateRows: 'auto auto minmax(0, 1fr)',
              height: '100%',
            }}
          >
            {showPythonError ? (
              <Dialog
                title="Error"
                isOpen={!!showPythonError}
                onClose={() => {
                  setShowPythonError(null);
                }}
                style={{width: '80vw'}}
              >
                <DialogBody>
                  <Box padding={{vertical: 12, horizontal: 24}}>
                    <PythonErrorInfo error={showPythonError} />
                  </Box>
                </DialogBody>
                <DialogFooter topBorder>
                  <Button
                    intent="primary"
                    onClick={() => {
                      setShowPythonError(null);
                    }}
                  >
                    Close
                  </Button>
                </DialogFooter>
              </Dialog>
            ) : null}
            <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
              <div
                style={{display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12}}
              >
                <Box flex={{direction: 'column', gap: 4}}>
                  <Subtitle2>Status</Subtitle2>
                  <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                    <Tag intent={intent}>
                      {tick?.requestedAssetMaterializationCount || 0} requested
                    </Tag>
                    {tick?.error ? (
                      <ButtonLink
                        onClick={() => {
                          setShowPythonError(tick.error!);
                        }}
                      >
                        View error
                      </ButtonLink>
                    ) : null}
                  </Box>
                </Box>
                <Box flex={{direction: 'column', gap: 4}}>
                  <Subtitle2>Timestamp</Subtitle2>
                  <div>
                    {tick ? (
                      <Timestamp timestamp={{unix: tick.timestamp}} dateTimeSeparator=" at " />
                    ) : (
                      '–'
                    )}
                  </div>
                </Box>
                <Box flex={{direction: 'column', gap: 4}}>
                  <Subtitle2>Duration</Subtitle2>
                  <div>
                    {tick?.endTimestamp
                      ? formatElapsedTime(tick.endTimestamp * 1000 - tick.timestamp * 1000)
                      : '–'}
                  </div>
                </Box>
              </div>
            </Box>
            <Box
              padding={{vertical: 12, horizontal: 24}}
              border={filteredAssetKeys.length > 0 ? undefined : 'bottom'}
            >
              <Subtitle2>Materializations requested</Subtitle2>
            </Box>
            {content}
          </div>
        }
      />
    );
  },
);

const AssetDetailRow = ({
  $start,
  $height,
  assetKey,
}: {
  $start: number;
  $height: number;
  assetKey: AssetKeyInput;
}) => {
  // TODO (after daniel adds new fields)
  return (
    <Row $start={$start} $height={$height}>
      <RowGrid border="bottom">
        <RowCell>
          <AssetLink path={assetKey.path} icon="asset" textStyle="middle-truncate" />
        </RowCell>
        <RowCell></RowCell>
        <RowCell></RowCell>
      </RowGrid>
    </Row>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
  > * {
    padding-top: 26px 0px;
  }
`;
