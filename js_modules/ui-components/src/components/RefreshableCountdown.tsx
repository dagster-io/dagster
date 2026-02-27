import {Box} from './Box';
import {Colors} from './Color';
import {Icon} from './Icon';
import {Tooltip} from './Tooltip';
import styles from './css/RefreshableCountdown.module.css';
import {secondsToCountdownTime} from './secondsToCountdownTime';

interface Props {
  refreshing: boolean;
  seconds?: number;
  onRefresh: () => void;
  dataDescription?: string;
}

export const RefreshableCountdown = (props: Props) => {
  const {refreshing, seconds, onRefresh, dataDescription = 'data'} = props;
  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <span
        style={{
          color: Colors.textLight(),
          fontVariantNumeric: 'tabular-nums',
          whiteSpace: 'nowrap',
        }}
      >
        {refreshing
          ? `Refreshing ${dataDescription}…`
          : seconds === undefined
            ? null
            : secondsToCountdownTime(seconds)}
      </span>
      <Tooltip content={<span style={{whiteSpace: 'nowrap'}}>Refresh now</span>} position="top">
        <button className={styles.refreshButton} onClick={onRefresh}>
          <Icon name="refresh" color={Colors.accentGray()} />
        </button>
      </Tooltip>
    </Box>
  );
};
