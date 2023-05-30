import {MockedProvider} from '@apollo/client/testing';
import {Box, ButtonGroup, Checkbox, JoinedButtons} from '@dagster-io/ui';
import React from 'react';

import {AutoMaterializePolicyType} from '../../graphql/types';
import {AssetAutomaterializePolicyPage} from '../AutoMaterializePolicyPage/AssetAutomaterializePolicyPage';
import {Evaluations, Policies} from '../__fixtures__/AutoMaterializePolicyPage.fixtures';

// eslint-disable-next-line import/no-default-export
export default {component: AssetAutomaterializePolicyPage};

const path = ['test'];

export const EmptyState = () => {
  return (
    <MockedProvider
      mocks={[Policies.NoAutomaterializeNoFreshnessPolicy(path), Evaluations.None(path)]}
    >
      <AssetAutomaterializePolicyPage assetKey={{path}} />
    </MockedProvider>
  );
};

export const Controlled = () => {
  const [policyType, setPolicyType] = React.useState<any>(AutoMaterializePolicyType.EAGER);
  const [freshnessPolicy, setFreshnessPolicy] = React.useState(true);

  const policyMock = React.useMemo(() => {
    if (policyType === 'None') {
      return freshnessPolicy
        ? Policies.NoAutomaterializeYesFreshnessPolicy(path)
        : Policies.NoAutomaterializeNoFreshnessPolicy(path);
    } else {
      return freshnessPolicy
        ? Policies.YesAutomaterializeYesFreshnessPolicy(path, policyType)
        : Policies.NoAutomaterializeYesFreshnessPolicy(path);
    }
  }, [freshnessPolicy, policyType]);

  return (
    <div key={policyType + freshnessPolicy.toString()}>
      <MockedProvider mocks={[policyMock, Evaluations.Some(path)]}>
        <div>
          <Box padding={24}>
            <Checkbox
              format="switch"
              label="Freshness policy"
              checked={freshnessPolicy}
              onChange={() => {
                setFreshnessPolicy((policy) => !policy);
              }}
            />
            <JoinedButtons>
              <ButtonGroup
                activeItems={new Set([policyType])}
                buttons={[
                  {id: AutoMaterializePolicyType.EAGER, label: 'Eager'},
                  {id: AutoMaterializePolicyType.LAZY, label: 'Lazy'},
                  {id: 'None', label: 'None'},
                ]}
                onClick={(id: string) => {
                  setPolicyType(id as any);
                }}
              />
            </JoinedButtons>
          </Box>
          <AssetAutomaterializePolicyPage assetKey={{path}} />
        </div>
      </MockedProvider>
    </div>
  );
};
