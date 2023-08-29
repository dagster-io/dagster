import {Box, Spinner, Tag} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetCheckExecutionResolvedStatus, AssetCheckSeverity} from '../../graphql/types';

export const AssetCheckStatusTag = ({
  status,
  severity,
  notChecked,
}: {
  status?: AssetCheckExecutionResolvedStatus;
  severity?: AssetCheckSeverity;
  notChecked?: boolean;
}) => {
  if (notChecked) {
    return <Tag>Not checked</Tag>;
  }
  const isWarn = severity === AssetCheckSeverity.WARN;
  switch (status) {
    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return (
        <Tag intent="primary">
          <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
            <Spinner purpose="body-text" />
            Running
          </Box>
        </Tag>
      );
    case AssetCheckExecutionResolvedStatus.FAILED:
      return (
        <Tag icon={isWarn ? 'warning_outline' : 'cancel'} intent={isWarn ? 'warning' : 'danger'}>
          Failed
        </Tag>
      );
    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
      return <Tag intent={isWarn ? 'warning' : 'danger'}>Execution failed</Tag>;
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return (
        <Tag icon="check_circle" intent="success">
          Passed
        </Tag>
      );
  }
  return null;
};
