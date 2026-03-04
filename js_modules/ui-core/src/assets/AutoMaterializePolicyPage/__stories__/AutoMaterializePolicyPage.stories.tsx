import {MockedProvider} from '@apollo/client/testing';

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
  return (
    <div>
      <MockedProvider
        mocks={[
          Evaluations.Some(path),
          Evaluations.SinglePartitioned(path, '9798'),
          Evaluations.SinglePartitioned(path, '28'),
        ]}
      >
        <div>
          <AssetAutomaterializePolicyPage assetKey={{path}} />
        </div>
      </MockedProvider>
    </div>
  );
};
