import {
  BaseTag,
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Tag,
  Tooltip,
  ifPlural,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {InstigationTickStatus} from '../graphql/types';
import {HistoryTickFragment} from '../instigation/types/InstigationUtils.types';

export type TickResultType = 'runs' | 'materializations';

type PropsForMaterializations = {
  tick: Pick<HistoryTickFragment, 'status' | 'requestedAssetMaterializationCount' | 'submittedAssetMaterializationCount' | 'error'>;
  tickResultType: 'materializations';
  isStuckStarted?: boolean;
};

type PropsForRuns = {
  tick: Pick<HistoryTickFragment, 'status' | 'skipReason' | 'runIds' | 'runKeys' | 'error'>;
  tickResultType: 'runs';
  isStuckStarted?: boolean;
};

export const TickStatusTag = ({
  tick,
  tickResultType,
  isStuckStarted,
}: PropsForMaterializations | PropsForRuns) => {
  const [showErrors, setShowErrors] = useState(false);
  const tag = useMemo(() => {
    const requestedItem = tickResultType === 'materializations' ? 'materialization' : 'run';
    const requestedCount =
      tickResultType === 'materializations'
        ? tick.requestedAssetMaterializationCount
        : tick.runIds.length;
    switch (tick.status) {
      case InstigationTickStatus.STARTED:
        return (
          <Tag intent="primary" icon={isStuckStarted ? undefined : 'spinner'}>
            {isStuckStarted ? 'In progress' : 'Evaluating'}
          </Tag>
        );
      case InstigationTickStatus.SKIPPED:
        const submittedCount =
          tickResultType === 'materializations'
            ? tick.submittedAssetMaterializationCount
            : tick.runIds.length;
        const tag = (
          <BaseTag
            fillColor={Colors.backgroundLighter()}
            label={`${submittedCount}/${requestedCount} requested ${requestedItem}${ifPlural(requestedCount, '', 's')} submitted`}
          />
        );
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
        const successTag = (
          <Tag intent="success">
            {requestedCount} {requestedItem}
            {ifPlural(requestedCount, '', 's')} requested
          </Tag>
        );
        if ('runKeys' in tick && tick.runKeys.length > tick.runIds.length) {
          const message = `${tick.runKeys.length} runs requested, but ${
            tick.runKeys.length - tick.runIds.length
          } skipped because the runs already exist for those requested keys.`;
          return (
            <Tooltip position="right" content={message}>
              {successTag}
            </Tooltip>
          );
        }
        return successTag;
    }
  }, [isStuckStarted, tick, tickResultType]);

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
