import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {LocationStateChangeEventType} from '../../graphql/types';
import {TestProvider} from '../../testing/TestProvider';
import {HIDDEN_REPO_KEYS} from '../../workspace/WorkspaceContext';
import {DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';
import {LeftNavRepositorySection} from '../LeftNavRepositorySection';

describe('Repository options', () => {
  const defaultMocks = {
    RepositoryLocation: () => ({
      name: () => 'bar',
      repositories: () => [...new Array(1)],
    }),
    Schedules: () => ({
      results: () => [],
    }),
    Sensors: () => ({
      results: () => [],
    }),
    LocationStateChangeEvent: () => ({
      eventType: () => LocationStateChangeEventType.LOCATION_UPDATED,
    }),
  };

  const locationOne = 'ipsum';
  const repoOne = 'lorem';
  const locationTwo = 'bar';
  const repoTwo = 'foo';
  const locationThree = 'abc_location';
  const repoThree = DUNDER_REPO_NAME;

  afterEach(() => {
    window.localStorage.clear();
  });

  it('Correctly displays the current repository state', async () => {
    const mocks = {
      Repository: () => ({
        name: () => 'foo',
        pipelines: () => [...new Array(1)],
        assetGroups: () => [],
      }),
      Pipeline: () => ({
        id: () => 'my_pipeline',
        name: () => 'my_pipeline',
        modes: () => [...new Array(1)],
        isAssetJob: () => false,
      }),
    };

    render(
      <TestProvider
        apolloProps={{mocks: [defaultMocks, mocks]}}
        routerProps={{initialEntries: ['/locations/foo@bar/etc']}}
      >
        <LeftNavRepositorySection />
      </TestProvider>,
    );

    const repoHeader = await screen.findByRole('button', {name: /foo/i});
    userEvent.click(repoHeader);

    await waitFor(() => {
      expect(screen.getByRole('link', {name: /my_pipeline/i})).toBeVisible();
    });
  });

  describe('localStorage', () => {
    const mocksWithOne = {
      Workspace: () => ({
        id: 'workspace',
        locationEntries: () => [
          {
            locationOrLoadError: {
              __typename: 'RepositoryLocation',
              name: locationOne,
              repositories: [{name: repoOne, pipelines: [...new Array(2)], assetGroups: []}],
            },
          },
        ],
      }),
    };

    const mocksWithThree = {
      Workspace: () => ({
        id: 'workspace',
        locationEntries: () => [
          {
            locationOrLoadError: {
              __typename: 'RepositoryLocation',
              name: locationOne,
              repositories: [{name: repoOne, pipelines: [...new Array(2)], assetGroups: []}],
            },
          },
          {
            locationOrLoadError: {
              __typename: 'RepositoryLocation',
              name: locationTwo,
              repositories: [{name: repoTwo, pipelines: [...new Array(4)], assetGroups: []}],
            },
          },
          {
            locationOrLoadError: {
              __typename: 'RepositoryLocation',
              name: locationThree,
              repositories: [{name: repoThree, pipelines: [...new Array(6)], assetGroups: []}],
            },
          },
        ],
      }),
    };

    it('initializes with first repo option, if one option and no localStorage', async () => {
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithOne]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      const repoHeader = await screen.findByRole('button', {name: /lorem/i});
      userEvent.click(repoHeader);

      await waitFor(() => {
        // Three links. Two jobs, one repo name at the bottom.
        expect(screen.getAllByRole('link')).toHaveLength(3);
      });
    });

    it(`initializes with one repo if it's the only one, even though it's hidden`, async () => {
      window.localStorage.setItem(HIDDEN_REPO_KEYS, `["${repoOne}:${locationOne}"]`);
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithOne]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      const repoHeader = await screen.findByRole('button', {name: /lorem/i});
      userEvent.click(repoHeader);

      await waitFor(() => {
        // Three links. Two jobs, one repo name at the bottom.
        expect(screen.getAllByRole('link')).toHaveLength(3);
      });
    });

    it('initializes with all repos visible, if multiple options and no localStorage', async () => {
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithThree]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      const loremHeader = await screen.findByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeVisible();
      const fooHeader = await screen.findByRole('button', {name: /foo/i});
      expect(fooHeader).toBeVisible();
      const dunderHeader = await screen.findByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeVisible();

      userEvent.click(loremHeader);
      userEvent.click(fooHeader);
      userEvent.click(dunderHeader);

      await waitFor(() => {
        // Twelve jobs total. No repo name link since multiple repos are visible.
        expect(screen.queryAllByRole('link')).toHaveLength(12);
      });
    });

    it('initializes with correct repo option, if `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(
        HIDDEN_REPO_KEYS,
        `["lorem:ipsum","${DUNDER_REPO_NAME}:abc_location"]`,
      );
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithThree]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      const fooHeader = await screen.findByRole('button', {name: /foo/i});
      userEvent.click(fooHeader);

      // `foo@bar` is visible, and has four jobs. Plus one for repo link at bottom.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(5);
      });
    });

    it('initializes with all repo options, no matching `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(HIDDEN_REPO_KEYS, '["hello:world"]');
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithThree]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      const loremHeader = await screen.findByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeVisible();
      const fooHeader = await screen.findByRole('button', {name: /foo/i});
      expect(fooHeader).toBeVisible();
      const dunderHeader = await screen.findByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeVisible();

      userEvent.click(loremHeader);
      userEvent.click(fooHeader);
      userEvent.click(dunderHeader);

      await waitFor(() => {
        // Twelve jobs total. No repo name link since multiple repos are visible.
        expect(screen.queryAllByRole('link')).toHaveLength(12);
      });
    });

    it('initializes empty, if all items in `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(
        HIDDEN_REPO_KEYS,
        `["lorem:ipsum", "foo:bar", "${DUNDER_REPO_NAME}:abc_location"]`,
      );
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithThree]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      const loremHeader = screen.queryByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeNull();
      const fooHeader = screen.queryByRole('button', {name: /foo/i});
      expect(fooHeader).toBeNull();
      const dunderHeader = screen.queryByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeNull();

      // No linked jobs or repos. Everything is hidden.
      await waitFor(() => {
        expect(screen.queryAllByRole('link')).toHaveLength(0);
      });
    });

    it('initializes empty, then shows options when they are added', async () => {
      const initialMocks = {
        Workspace: () => ({
          id: 'workspace',
          locationEntries: () => [],
        }),
      };

      const {rerender} = render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, initialMocks]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      // Zero repositories, so zero pipelines.
      await waitFor(() => {
        expect(screen.queryAllByRole('link')).toHaveLength(0);
      });

      rerender(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithThree]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      const loremHeader = await screen.findByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeVisible();
      const fooHeader = await screen.findByRole('button', {name: /foo/i});
      expect(fooHeader).toBeVisible();
      const dunderHeader = await screen.findByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeVisible();

      userEvent.click(loremHeader);
      userEvent.click(fooHeader);
      userEvent.click(dunderHeader);

      // After repositories are added and expanded, all become visible.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(12);
      });
    });

    it('initializes with options, then shows empty if they are removed', async () => {
      const mocksAfterRemoval = {
        Workspace: () => ({
          id: 'workspace',
          locationEntries: () => [],
        }),
      };

      const {rerender} = render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithOne]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      const loremHeader = await screen.findByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeVisible();
      userEvent.click(loremHeader);

      // Three links: two jobs, one repo link at bottom.
      await waitFor(() => {
        expect(screen.queryAllByRole('link')).toHaveLength(3);
      });

      rerender(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksAfterRemoval]}}
          routerProps={{initialEntries: ['/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      // After repositories are removed, there are none displayed.
      await waitFor(() => {
        expect(screen.queryAllByRole('link')).toHaveLength(0);
      });
    });
  });

  describe('Asset groups', () => {
    const mocks = {
      AssetGroup: () => ({
        groupName: () => 'my_asset_group',
      }),
      Pipeline: () => ({
        id: () => 'my_pipeline',
        name: () => 'my_pipeline',
        modes: () => [...new Array(1)],
        isAssetJob: () => false,
      }),
      Workspace: () => ({
        id: 'workspace',
        locationEntries: () => [
          {
            locationOrLoadError: {
              __typename: 'RepositoryLocation',
              name: locationOne,
              repositories: [
                {name: repoOne, pipelines: [...new Array(1)], assetGroups: [...new Array(1)]},
              ],
            },
          },
        ],
      }),
    };

    it('renders asset groups alongside jobs', async () => {
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocks]}}
          routerProps={{initialEntries: ['/locations/foo@bar/etc']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      const repoHeader = await screen.findByRole('button', {name: /lorem/i});
      userEvent.click(repoHeader);

      await waitFor(() => {
        expect(screen.getByRole('link', {name: /my_pipeline/i})).toBeVisible();
        expect(screen.getByRole('link', {name: /my_asset_group/i})).toBeVisible();
      });
    });
  });
});
