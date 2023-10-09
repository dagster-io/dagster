import {Tag} from '@dagster-io/ui-components';
import React from 'react';

import {DagsterTag} from '../runs/RunTag';

export const RunlessEventTag: React.FC<{
  tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
}> = ({tags}) => {
  const user = tags.find((t) => t.key === DagsterTag.User);

  return user ? <Tag>Reported by {user.value}</Tag> : <Tag>Reported</Tag>;
};
