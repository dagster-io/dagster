import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {AssetGroupSelector} from '../../graphql/types';
import {DUNDER_REPO_NAME, buildRepoAddress} from '../../workspace/buildRepoAddress';
import {AssetGroupTags} from '../AssetGroupRoot';
import * as AutomationPolicySensorFlag from '../AutomationPolicySensorFlag';
import {
  GROUP_NAME,
  LOCATION_NAME,
  assetGroupWithAMP,
  assetGroupWithoutAMP,
} from '../__fixtures__/AssetGroupTags.fixtures';

jest.mock('../useAutomaterializeDaemonStatus', () => ({
  useAutomaterializeDaemonStatus: jest.fn(() => ({
    loading: false,
    setPaused: jest.fn(),
    paused: false,
    refetch: jest.fn(),
  })),
}));

describe('AssetGroupTags', () => {
  const repoAddress = buildRepoAddress(DUNDER_REPO_NAME, LOCATION_NAME);
  const groupSelector: AssetGroupSelector = {
    groupName: GROUP_NAME,
    repositoryName: DUNDER_REPO_NAME,
    repositoryLocationName: LOCATION_NAME,
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders asset group tag', async () => {
    jest
      .spyOn(AutomationPolicySensorFlag, 'useAutomationPolicySensorFlag')
      .mockReturnValue('has-global-amp');

    render(
      <MemoryRouter>
        <MockedProvider mocks={[assetGroupWithoutAMP]}>
          <AssetGroupTags repoAddress={repoAddress} groupSelector={groupSelector} />
        </MockedProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText(/asset group in/i)).toBeVisible();
    expect(await screen.findByRole('link', {name: /my_location/i})).toBeVisible();
  });

  it('renders global AMP tag', async () => {
    jest
      .spyOn(AutomationPolicySensorFlag, 'useAutomationPolicySensorFlag')
      .mockReturnValue('has-global-amp');

    render(
      <MemoryRouter>
        <MockedProvider mocks={[assetGroupWithAMP]}>
          <AssetGroupTags repoAddress={repoAddress} groupSelector={groupSelector} />
        </MockedProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText(/asset group in/i)).toBeVisible();
    expect(await screen.findByRole('link', {name: /my_location/i})).toBeVisible();
    expect(await screen.findByRole('link', {name: /auto\-materialize on/i})).toBeVisible();
  });

  it('does not render global AMP tag when sensors are turned on', async () => {
    jest
      .spyOn(AutomationPolicySensorFlag, 'useAutomationPolicySensorFlag')
      .mockReturnValue('has-sensor-amp');

    render(
      <MemoryRouter>
        <MockedProvider mocks={[assetGroupWithAMP]}>
          <AssetGroupTags repoAddress={repoAddress} groupSelector={groupSelector} />
        </MockedProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText(/asset group in/i)).toBeVisible();
    expect(await screen.findByRole('link', {name: /my_location/i})).toBeVisible();
    expect(await screen.queryByRole('link', {name: /auto\-materialize on/i})).toBeNull();
  });
});
