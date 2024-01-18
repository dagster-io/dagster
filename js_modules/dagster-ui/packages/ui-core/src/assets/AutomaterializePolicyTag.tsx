import groupBy from 'lodash/groupBy';
import React from 'react';

import {Box, Tag} from '@dagster-io/ui-components';

import {AutoMaterializePolicyType, AutoMaterializeRule} from '../graphql/types';

export const AutomaterializePolicyTag = ({
  policy,
}: {
  policy: {
    policyType: AutoMaterializePolicyType;
  };
}) => <Tag>{policy.policyType === AutoMaterializePolicyType.LAZY ? 'Lazy' : 'Eager'}</Tag>;

export const automaterializePolicyDescription = (policy: {
  policyType: AutoMaterializePolicyType;
  rules: Pick<AutoMaterializeRule, 'description' | 'decisionType'>[];
}) => {
  const {MATERIALIZE, SKIP, DISCARD} = groupBy(policy.rules, (rule) => rule.decisionType);
  return (
    <Box flex={{direction: 'column', gap: 12}}>
      This asset will be automatically materialized if it is:
      <ul style={{paddingLeft: 20, margin: 0}}>
        {MATERIALIZE?.map((rule) => <li key={rule.description}>{rule.description}</li>)}
      </ul>
      and it is not:
      <ul style={{paddingLeft: 20, margin: 0}}>
        {SKIP?.map((rule) => <li key={rule.description}>{rule.description}</li>)}
      </ul>
      {DISCARD && DISCARD.length > 0 && (
        <>
          Partitions may be discarded and require a backfill to materialize if it:
          <ul style={{paddingLeft: 20, margin: 0}}>
            {DISCARD.map((rule) => (
              <li key={rule.description}>{rule.description}</li>
            ))}
          </ul>
        </>
      )}
    </Box>
  );
};
