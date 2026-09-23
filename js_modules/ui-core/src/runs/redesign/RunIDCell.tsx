import {Text, Tooltip} from '@dagster-io/ui-components';

import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {shortenId} from '../../util/shortenId';

type Props = {
  entry: MappedRunsFeedEntry;
};

export const RunIDCell = ({entry}: Props) => {
  const shortId = shortenId(entry.id);
  return (
    <Tooltip content={entry.id} placement="top" canShow={shortId !== entry.id}>
      <Text family="mono" size={14} color="textLighter">
        {shortId}
      </Text>
    </Tooltip>
  );
};
