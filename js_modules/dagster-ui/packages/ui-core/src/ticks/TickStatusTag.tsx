import {
  Tag,
  Dialog,
  DialogBody,
  DialogFooter,
  Button,
  BaseTag,
  Colors,
  Box,
  ButtonLink,
  Tooltip,
} from '@dagster-io/ui-components';
import React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {InstigationTickStatus} from '../graphql/types';
import {HistoryTickFragment} from '../instigation/types/InstigationUtils.types';

export const TickStatusTag = ({
  tick,
}: {
  tick:
    | Pick<AssetDaemonTickFragment, 'status' | 'error' | 'requestedAssetMaterializationCount'>
    | Pick<HistoryTickFragment, 'status' | 'skipReason' | 'runIds' | 'runKeys' | 'error'>;
}) => {
  const [showErrors, setShowErrors] = React.useState(false);
  const tag = React.useMemo(() => {
    const isAssetDaemonTick = 'requestedAssetMaterializationCount' in tick;
    switch (tick.status) {
      case InstigationTickStatus.STARTED:
        return (
          <Tag intent="primary" icon="spinner">
            Evaluating
          </Tag>
        );
      case InstigationTickStatus.SKIPPED:
        const tag = <BaseTag fillColor={Colors.Olive50} label="0 requested" />;
        if ('runKeys' in tick && tick.runKeys.length) {
          const message = `${tick.runKeys.length} runs requested, but skipped because the runs already exist for the requested keys.`;
          return (
            <Tooltip position="right" content={message}>
              {tag}
            </Tooltip>
          );
        }
        if ('skipReason' in tick && tick.skipReason) {
          return (
            <Tooltip position="right" content={tick.skipReason} targetTagName="div">
              {tag}
            </Tooltip>
          );
        }
        return tag;
      case InstigationTickStatus.FAILURE:
        return (
          <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
            <Tag intent="danger">Failure</Tag>
            {tick.error ? (
              <ButtonLink
                onClick={() => {
                  setShowErrors(true);
                }}
              >
                View
              </ButtonLink>
            ) : null}
          </Box>
        );
      case InstigationTickStatus.SUCCESS:
        const count = isAssetDaemonTick
          ? tick.requestedAssetMaterializationCount
          : tick.runIds.length;
        return <Tag intent="success">{count} requested</Tag>;
    }
  }, [tick]);

  return (
    <>
      {tag}
      {tick.error ? (
        <Dialog isOpen={showErrors} title="Error" style={{width: '80vw'}}>
          <DialogBody>
            <PythonErrorInfo error={tick.error} />
          </DialogBody>
          <DialogFooter topBorder>
            <Button
              intent="primary"
              onClick={() => {
                setShowErrors(false);
              }}
            >
              Close
            </Button>
          </DialogFooter>
        </Dialog>
      ) : null}
    </>
  );
};
