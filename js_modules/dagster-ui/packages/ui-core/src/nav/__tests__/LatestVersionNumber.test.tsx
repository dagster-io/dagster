import {MockedProvider} from '@apollo/client/testing';
import {screen} from '@testing-library/dom';
import {render} from '@testing-library/react';

import {LatestVersionNumber} from '../LatestVersionNumber';

// Mock fetch globally
global.fetch = jest.fn();

describe('LatestVersionNumber', () => {
  beforeEach(() => {
    // Clear mock before each test
    (global.fetch as jest.Mock).mockClear();
    sessionStorage.clear();
  });

  it('renders the latest version number', async () => {
    // Mock the GitHub API response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        tag_name: '1.2.34',
      }),
    });

    render(
      <MockedProvider mocks={[]}>
        <LatestVersionNumber />
      </MockedProvider>,
    );

    expect(await screen.findByText(/1\.2\.34/)).toBeVisible();

    // Verify fetch was called with correct URL
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.github.com/repos/dagster-io/dagster/releases/latest',
    );
  });

  it('uses cached version from sessionStorage', async () => {
    // Pre-populate sessionStorage
    sessionStorage.setItem('dagster_latest_version', '42.42.42');

    render(
      <MockedProvider mocks={[]}>
        <LatestVersionNumber />
      </MockedProvider>,
    );

    expect(await screen.findByText(/42\.42\.42/)).toBeVisible();

    // Verify fetch was NOT called
    expect(global.fetch).not.toHaveBeenCalled();
  });
});
