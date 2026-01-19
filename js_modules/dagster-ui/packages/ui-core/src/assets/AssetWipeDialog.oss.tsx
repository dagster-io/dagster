// eslint-disable-next-line no-restricted-imports
import {ProgressBar} from '@blueprintjs/core';
import {
  Body1,
  Box,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  Group,
  ifPlural,
} from '@dagster-io/ui-components';
import {memo, useMemo} from 'react';

import {RefetchQueriesFunction} from '../apollo-client';
import {VirtualizedSimpleAssetKeyList} from './VirtualizedSimpleAssetKeyList';
import {asAssetPartitionRangeInput} from './asInput';
import {useWipeAssets} from './useWipeAssets';
import {AssetKeyInput} from '../graphql/types';
import {NavigationBlock} from '../runs/NavigationBlock';
import {numberFormatter} from '../ui/formatters';

export const AssetWipeDialog = memo(
  (props: {
    assetKeys: AssetKeyInput[];
    isOpen: boolean;
    onClose: () => void;
    onComplete?: () => void;
    requery?: RefetchQueriesFunction;
  }) => {
    return (
      <Dialog
        isOpen={props.isOpen}
        title="清除物化数据"
        onClose={props.onClose}
        style={{width: '80vw', maxWidth: '1200px', minWidth: '600px'}}
      >
        <AssetWipeDialogInner {...props} />
      </Dialog>
    );
  },
);

export const AssetWipeDialogInner = memo(
  ({
    assetKeys,
    onClose,
    onComplete,
    requery,
  }: {
    assetKeys: AssetKeyInput[];
    onClose: () => void;
    onComplete?: () => void;
    requery?: RefetchQueriesFunction;
  }) => {
    const {wipeAssets, isWiping, isDone, wipedCount, failedCount} = useWipeAssets({
      refetchQueries: requery,
      onClose,
      onComplete,
    });

    const content = useMemo(() => {
      if (isDone) {
        return (
          <Box flex={{direction: 'column'}}>
            {wipedCount ? <Body1>{numberFormatter.format(wipedCount)} 已清除</Body1> : null}
            {failedCount ? <Body1>{numberFormatter.format(failedCount)} 失败</Body1> : null}
          </Box>
        );
      } else if (!isWiping) {
        return (
          <Group direction="column" spacing={16}>
            <div>
              确定要清除 {numberFormatter.format(assetKeys.length)} 个资产的物化数据吗？
            </div>
            <VirtualizedSimpleAssetKeyList assetKeys={assetKeys} style={{maxHeight: '50vh'}} />
            <div>
              仅由历史物化数据定义的资产将从资产目录中消失。
              软件定义的资产将保留，除非其定义也被删除。
            </div>
            <strong>此操作无法撤销。</strong>
          </Group>
        );
      }
      const value = assetKeys.length > 0 ? (wipedCount + failedCount) / assetKeys.length : 1;
      return (
        <Box flex={{gap: 8, direction: 'column'}}>
          <div>正在清除...</div>
          <ProgressBar intent="primary" value={Math.max(0.1, value)} animate={value < 1} />
          <NavigationBlock message="清除操作进行中，请勿离开此页面。" />
        </Box>
      );
    }, [isDone, isWiping, assetKeys, wipedCount, failedCount]);

    return (
      <>
        <DialogBody>{content}</DialogBody>
        <DialogFooter topBorder>
          <Button intent={isDone ? 'primary' : 'none'} onClick={onClose}>
            {isDone ? '完成' : '取消'}
          </Button>
          {isDone ? null : (
            <Button
              intent="danger"
              onClick={() => wipeAssets(assetKeys.map((key) => asAssetPartitionRangeInput(key)))}
              disabled={isWiping}
              loading={isWiping}
            >
              清除
            </Button>
          )}
        </DialogFooter>
      </>
    );
  },
);
