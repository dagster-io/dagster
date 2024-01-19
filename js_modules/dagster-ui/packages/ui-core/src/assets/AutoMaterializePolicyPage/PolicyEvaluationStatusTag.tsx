import {Tag} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetConditionEvaluationStatus} from './types';
import {assertUnreachable} from '../../app/Util';

export const PolicyEvaluationStatusTag = ({status}: {status: AssetConditionEvaluationStatus}) => {
  switch (status) {
    case AssetConditionEvaluationStatus.FALSE:
      return (
        <Tag intent="warning" icon="cancel">
          False
        </Tag>
      );
    case AssetConditionEvaluationStatus.TRUE:
      return (
        <Tag intent="success" icon="check_circle">
          True
        </Tag>
      );
    case AssetConditionEvaluationStatus.SKIPPED:
      return <Tag intent="none">Skipped</Tag>;
    default:
      return assertUnreachable(status);
  }
};
