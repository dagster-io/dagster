import {Text, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import styles from './css/RunIDCell.module.css';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {shortenId} from '../../util/shortenId';

type Props = {
  entry: MappedRunsFeedEntry;
};

export const RunIDCell = ({entry}: Props) => {
  const shortId = shortenId(entry.id);
  const entryTypeLabel = entry.__typename === 'PartitionBackfill' ? 'Backfill' : 'Run';
  return (
    <Tooltip content={entry.id} placement="top" canShow={shortId !== entry.id}>
      <Link to={entry.href} className={styles.link} aria-label={`${entryTypeLabel} ${shortId}`}>
        <Text family="mono" size={14} color="textLighter">
          {shortId}
        </Text>
      </Link>
    </Tooltip>
  );
};
