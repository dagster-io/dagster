import {MockedProvider} from '@apollo/client/testing';
import {Box, ButtonGroup, Checkbox, JoinedButtons} from '@dagster-io/ui-components';
import {useState} from 'react';

import {AutoMaterializePolicyType} from '../../../graphql/types';
import {AssetAutomaterializePolicyPage} from '../AssetAutomaterializePolicyPage';
import {Evaluations} from '../__fixtures__/AutoMaterializePolicyPage.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize',
  component: AssetAutomaterializePolicyPage,
};

const path = ['test'];

export const EmptyState = () => {
  return (
    <MockedProvider mocks={[Evaluations.None(path, true)]}>
      <AssetAutomaterializePolicyPage assetKey={{path}} />
    </MockedProvider>
  );
};

export const Errors = () => {
  return (
    <MockedProvider mocks={[Evaluations.Errors(path), Evaluations.Errors(path, true)]}>
      <AssetAutomaterializePolicyPage assetKey={{path}} />
    </MockedProvider>
  );
};

export const Controlled = () => {
  const [policyType, setPolicyType] = useState<any>(AutoMaterializePolicyType.EAGER);
  const [freshnessPolicy, setFreshnessPolicy] = useState(true);

  return (
    <div key={freshnessPolicy.toString()}>
      <MockedProvider
        mocks={[
          Evaluations.Some(path),
          Evaluations.SinglePartitioned(path, '9798'),
          Evaluations.SinglePartitioned(path, '28'),
        ]}
      >
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
