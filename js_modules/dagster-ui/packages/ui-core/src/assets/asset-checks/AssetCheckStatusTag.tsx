import {Box, Spinner, Tag} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetCheckExecutionStatus} from '../../graphql/types';

export const AssetCheckStatusTag = ({
  status,
  notChecked,
}: {
  status?: AssetCheckExecutionStatus;
  notChecked?: boolean;
}) => {
  if (notChecked) {
    return <Tag>Not checked</Tag>;
  }
  switch (status) {
    case AssetCheckExecutionStatus.PLANNED:
      return (
        <Tag intent="primary">
          <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
            <Spinner purpose="body-text" />
            Running
          </Box>
        </Tag>
      );
    case AssetCheckExecutionStatus.FAILURE:
      return (
        <Tag icon="cancel" intent="danger">
          Failed
        </Tag>
      );
    // case 'error':
    //   return (
    //     <Tag icon="warning_outline" intent="danger">
    //       Execution failed
    //     </Tag>
    //   );
    case AssetCheckExecutionStatus.SUCCESS:
      return (
        <Tag icon="check_circle" intent="success">
          Passed
        </Tag>
      );
  }
  return null;
};
