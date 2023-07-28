import {Tag} from '@dagster-io/ui';
import React from 'react';

import {AutoMaterializePolicyType} from '../graphql/types';

export const AutomaterializePolicyTag: React.FC<{
  policy: {
    policyType: AutoMaterializePolicyType;
  };
}> = ({policy}) => (
  <Tag>{policy.policyType === AutoMaterializePolicyType.LAZY ? 'Lazy' : 'Eager'}</Tag>
);

export const automaterializePolicyDescription = (policy: {
  policyType: AutoMaterializePolicyType;
}) => (
  <>
    This asset is automatically re-materialized when at least one of the following are true:
    <ul style={{paddingLeft: 20}}>
      <li>it is missing</li>
      <li>it has a freshness policy that requires more up-to-date data</li>
      <li>any of its descendants have a freshness policy that require more up-to-date data</li>
      {policy.policyType === AutoMaterializePolicyType.EAGER && (
        <li>any of its parent assets / partitions have newer data</li>
      )}
    </ul>
    and none of the following are true:
    <ul style={{paddingLeft: 20, marginBottom: 0}}>
      <li>any of its parent assets / partitions are missing</li>
      <li>any of its ancestor assets / partitions have ancestors of their own with newer data</li>
    </ul>
  </>
);
