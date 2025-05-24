import {Box} from '@dagster-io/ui-components';
import styles from './BackfillOverviewDetails.module.css';

import {BackfillStatusTagForPage} from './BackfillStatusTagForPage';
import {LiveDuration} from './LiveDuration';
import {TargetPartitionsDisplay} from './TargetPartitionsDisplay';
import {Timestamp} from '../../app/time/Timestamp';
import {testId} from '../../testing/testId';

export const BackfillOverviewDetails = ({backfill}: {backfill: any}) => (
  <Box
    padding={24}
    flex={{
      direction: 'row',
      justifyContent: 'space-between',
      wrap: 'nowrap',
      alignItems: 'center',
    }}
    data-testid={testId('backfill-page-details')}
  >
    <Detail
      label="Created"
      detail={
        <Timestamp
          timestamp={{ms: Number(backfill.timestamp * 1000)}}
          timeFormat={{showSeconds: true, showTimezone: false}}
        />
      }
    />
    <Detail
      label="Duration"
      detail={
        <LiveDuration
          start={backfill.timestamp * 1000}
          end={backfill.endTimestamp ? backfill.endTimestamp * 1000 : null}
        />
      }
    />
    <Detail
      label="Partition selection"
      detail={
        <TargetPartitionsDisplay
          targetPartitionCount={backfill.numPartitions || 0}
          targetPartitions={backfill.assetBackfillData?.rootTargetedPartitions}
        />
      }
    />
    <Detail label="Status" detail={<BackfillStatusTagForPage backfill={backfill} />} />
  </Box>
);

const Detail = ({label, detail}: {label: JSX.Element | string; detail: JSX.Element | string}) => (
  <Box flex={{direction: 'column', gap: 4}} style={{minWidth: '280px'}}>
    <div className={styles.label}>{label}</div>
    <div>{detail}</div>
  </Box>
);
