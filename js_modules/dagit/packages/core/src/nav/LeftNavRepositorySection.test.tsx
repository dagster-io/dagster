import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';
import {LocationStateChangeEventType} from '../types/globalTypes';

import {LeftNavRepositorySection, HIDDEN_REPO_KEYS} from './LeftNavRepositorySection';

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

  it('Correctly displays the current repository state', async () => {
    const mocks = {
      Repository: () => ({
        name: () => 'foo',
        pipelines: () => [...new Array(1)],
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
        routerProps={{initialEntries: ['/workspace/foo@bar/etc']}}
      >
        <LeftNavRepositorySection />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole('link', {
          name: /my_pipeline/i,
        }),
      ).toBeVisible();
    });
  });

  describe('localStorage', () => {
    beforeEach(() => {
      window.localStorage.clear();
    });

    const locationOne = 'ipsum';
    const repoOne = 'lorem';
    const locationTwo = 'bar';
    const repoTwo = 'foo';

    const mocksWithOne = {
      Workspace: () => ({
        locationEntries: () => [
          {
            locationOrLoadError: {
              __typename: 'RepositoryLocation',
              name: locationOne,
              repositories: [{name: repoOne, pipelines: [...new Array(2)]}],
            },
          },
        ],
      }),
    };

    const mocksWithTwo = {
      Workspace: () => ({
        locationEntries: () => [
          {
            locationOrLoadError: {
              __typename: 'RepositoryLocation',
              name: locationOne,
              repositories: [{name: repoOne, pipelines: [...new Array(2)]}],
            },
          },
          {
            locationOrLoadError: {
              __typename: 'RepositoryLocation',
              name: locationTwo,
              repositories: [{name: repoTwo, pipelines: [...new Array(4)]}],
            },
          },
        ],
      }),
    };

    it('initializes with first repo option, if one option and no localStorage', async () => {
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithOne]}}
          routerProps={{initialEntries: ['/instance/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      await waitFor(() => {
        // Three links. One for repo, two for pipelines.
        expect(screen.getAllByRole('link')).toHaveLength(3);
      });
    });

    it(`initializes with one repo if it's the only one, even though it's hidden`, async () => {
      window.localStorage.setItem(HIDDEN_REPO_KEYS, `["${repoOne}:${locationOne}"]`);
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithOne]}}
          routerProps={{initialEntries: ['/instance/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      await waitFor(() => {
        // Three links. One for repo, two for pipelines.
        expect(screen.getAllByRole('link')).toHaveLength(3);
      });
    });

    it('initializes empty, if multiple options and no localStorage', async () => {
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithTwo]}}
          routerProps={{initialEntries: ['/instance/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      await waitFor(() => {
        // We have multiple options and select none by default. Empty.
        expect(screen.queryAllByRole('link')).toHaveLength(0);
      });
    });

    it('initializes with correct repo option, if `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(HIDDEN_REPO_KEYS, '["lorem:ipsum"]');
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithTwo]}}
          routerProps={{initialEntries: ['/instance/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      // `foo@bar` is visible, and has four pipelines. Plus one for repo.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(5);
      });
    });

    it('initializes with all repo options, no matching `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(HIDDEN_REPO_KEYS, '["hello:world"]');
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithTwo]}}
          routerProps={{initialEntries: ['/instance/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      // All repos visible. `lorem@ipsum` has two pipelines, `foo@bar` has four.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(6);
      });
    });

    it('initializes empty, if all items in `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(HIDDEN_REPO_KEYS, '["lorem:ipsum", "foo:bar"]');
      render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithTwo]}}
          routerProps={{initialEntries: ['/instance/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      // No links.
      await waitFor(() => {
        expect(screen.queryAllByRole('link')).toHaveLength(0);
      });
    });

    it('initializes empty, then shows options when they are added', async () => {
      const initialMocks = {
        Workspace: () => ({
          locationEntries: () => [],
        }),
      };

      const {rerender} = render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, initialMocks]}}
          routerProps={{initialEntries: ['/instance/runs']}}
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
          apolloProps={{mocks: [defaultMocks, mocksWithTwo]}}
          routerProps={{initialEntries: ['/instance/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      // After repositories are added, all become visible.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(6);
      });
    });

    it('initializes with options, then shows empty if they are removed', async () => {
      const mocksAfterRemoval = {
        Workspace: () => ({
          locationEntries: () => [],
        }),
      };

      const {rerender} = render(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksWithOne]}}
          routerProps={{initialEntries: ['/instance/runs']}}
        >
          <LeftNavRepositorySection />
        </TestProvider>,
      );

      // Three links: two pipelines, one repo.
      await waitFor(() => {
        expect(screen.queryAllByRole('link')).toHaveLength(3);
      });

      rerender(
        <TestProvider
          apolloProps={{mocks: [defaultMocks, mocksAfterRemoval]}}
          routerProps={{initialEntries: ['/instance/runs']}}
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
});
