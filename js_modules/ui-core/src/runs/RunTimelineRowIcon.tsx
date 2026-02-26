import {Icon} from '@dagster-io/ui-components';

import {RowObjectType} from './RunTimelineTypes';
import {assertUnreachable} from '../app/Util';
import {TagIcon} from '../graph/OpTags';

export const RunTimelineRowIcon = ({type}: {type: RowObjectType | 'airflow'}) => {
  switch (type) {
    case 'asset':
      return <Icon name="asset" />;
    case 'job':
      return <Icon name="job" />;
    case 'manual':
      return <Icon name="account_circle" />;
    case 'schedule':
      return <Icon name="schedule" />;
    case 'sensor':
      return <Icon name="sensors" />;
    case 'legacy-amp':
      return <Icon name="sensors" />;
    case 'airflow':
      return <TagIcon label="airflow" />;
    default:
      return assertUnreachable(type);
  }
};
