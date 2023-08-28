import {Box, Spinner, Tag} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetCheckExecutionStatus, AssetCheckSeverity} from '../../graphql/types';

export const AssetCheckStatusTag = ({
  status,
  severity,
  notChecked,
}: {
  status?: AssetCheckExecutionStatus;
  severity?: AssetCheckSeverity;
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
      const isWarn = severity === AssetCheckSeverity.WARN;
      return (
        <Tag icon={isWarn ? 'warning_outline' : 'cancel'} intent={isWarn ? 'warning' : 'danger'}>
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
