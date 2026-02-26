import {Box, DialogHeader} from '@dagster-io/ui-components';
import {memo} from 'react';

import {AssetDaemonTickFragment} from './types/AssetDaemonTicksQuery.types';
import {Timestamp} from '../../app/time/Timestamp';
import {InstigationTickStatus} from '../../graphql/types';
import {TickDetailSummary} from '../../instigation/TickDetailsDialog';
import {TickMaterializationsTable} from '../../instigation/TickMaterializationsTable';
import {AssetKeysDialog} from '../AutoMaterializePolicyPage/AssetKeysDialog';

export const AutomaterializationTickDetailDialog = memo(
  ({
    tick,
    isOpen,
    close,
  }: {
    tick: AssetDaemonTickFragment | null;
    isOpen: boolean;
    close: () => void;
  }) => {
    return (
      <AssetKeysDialog
        isOpen={isOpen}
        setIsOpen={close}
        height={400}
        header={
          <DialogHeader
            label={
              tick ? (
                <div>
                  <Timestamp timestamp={{unix: tick.timestamp}} timeFormat={{showTimezone: true}} />
                </div>
              ) : (
                ''
              )
            }
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
            <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
              {tick ? <TickDetailSummary tick={tick} tickResultType="materializations" /> : null}
            </Box>
            {tick?.status === InstigationTickStatus.STARTED ? null : (
              <TickMaterializationsTable tick={tick} />
            )}
          </div>
        }
      />
    );
  },
);
