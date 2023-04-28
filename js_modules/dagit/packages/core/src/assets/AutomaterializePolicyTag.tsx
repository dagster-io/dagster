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
    This asset is automatically re-materialized when:
    <ul style={{paddingLeft: 20, marginBottom: 0}}>
      <li>it is missing</li>
      <li>it or any of its children have a freshness policy that require more up-to-date data</li>
      {policy.policyType === AutoMaterializePolicyType.EAGER && (
        <li>any of its parent assets / partitions have been updated more recently than it has</li>
      )}
    </ul>
  </>
);
