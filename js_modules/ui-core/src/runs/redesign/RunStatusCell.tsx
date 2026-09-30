import {Box, Icon, Popover, Spinner, Text, Tooltip} from '@dagster-io/ui-components';

import styles from './css/RunStatusCell.module.css';
import {getRunStatusDisplay} from './getRunStatusDisplay';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {RunStats} from '../RunStats';

type Props = {
  entry: MappedRunsFeedEntry;
};

export const RunStatusCell = ({entry}: Props) => {
  const {icon, iconColor, label, isPulsing} = getRunStatusDisplay(entry);

  const statusIcon = (
    <Box flex={{alignItems: 'center', shrink: 0}} role="img" aria-label={label}>
      {icon === 'spinner' ? (
        <Spinner purpose="body-text" fillColor={iconColor} title={label} />
      ) : (
        <Icon name={icon} color={iconColor} className={isPulsing ? styles.pulse : undefined} />
      )}
    </Box>
  );

  return entry.__typename === 'Run' ? (
    <Popover
      interactionKind="hover"
      usePortal
      position="bottom-left"
      hoverOpenDelay={100}
      // Hover-only, so the icon adds no tab stop.
      openOnTargetFocus={false}
      content={
        <>
          <Text as="div" size={12} weight={600} className={styles.popoverHeading}>
            {label}
          </Text>
          <RunStats runId={entry.id} />
        </>
      }
    >
      {statusIcon}
    </Popover>
  ) : (
    <Tooltip content={label} placement="top">
      {statusIcon}
    </Tooltip>
  );
};
