import * as React from 'react';
import {MockedProvider} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {
  HIDDEN_REPO_KEYS,
  WorkspaceContext,
  WorkspaceProvider,
} from '../../workspace/WorkspaceContext';
import {DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';
import {LeftNavRepositorySection} from '../LeftNavRepositorySection';
import {
  buildWorkspaceQueryWithOneLocation,
  buildWorkspaceQueryWithOneLocationAndAssetGroup,
  buildWorkspaceQueryWithThreeLocations,
  buildWorkspaceQueryWithZeroLocations,
} from '../__fixtures__/LeftNavRepositorySection.fixtures';

jest.mock('../RepositoryLocationStateObserver', () => ({
  RepositoryLocationStateObserver: () => <div />,
}));

describe('Repository options', () => {
  const locationOne = 'ipsum';
  const repoOne = 'lorem';

  let nativeGBRC: any;

  beforeAll(() => {
    nativeGBRC = window.Element.prototype.getBoundingClientRect;
    window.Element.prototype.getBoundingClientRect = jest
      .fn()
      .mockReturnValue({height: 400, width: 400});
  });

  afterAll(() => {
    window.Element.prototype.getBoundingClientRect = nativeGBRC;
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it('Correctly displays the current repository state', async () => {
    render(
      <MemoryRouter initialEntries={['/locations/foo@bar/etc']}>
        <MockedProvider mocks={[buildWorkspaceQueryWithOneLocation()]}>
          <WorkspaceProvider>
            <LeftNavRepositorySection />
          </WorkspaceProvider>
        </MockedProvider>
      </MemoryRouter>,
    );

    const repoHeader = await screen.findByRole('button', {name: /lorem/i});
    await userEvent.click(repoHeader);

    await waitFor(() => {
      expect(screen.getByRole('link', {name: /my_pipeline/i})).toBeVisible();
    });
  });

  describe('localStorage', () => {
    it('initializes with first repo option, if one option and no localStorage', async () => {
      render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider mocks={[buildWorkspaceQueryWithOneLocation()]}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const repoHeader = await screen.findByRole('button', {name: /lorem/i});
      await userEvent.click(repoHeader);

      await waitFor(() => {
        // Three links. Two jobs, one repo name at the bottom.
        expect(screen.getAllByRole('link')).toHaveLength(3);
      });
    });

    it(`initializes with one repo if it's the only one, even though it's hidden`, async () => {
      window.localStorage.setItem(HIDDEN_REPO_KEYS, `["${repoOne}:${locationOne}"]`);
      render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider mocks={[buildWorkspaceQueryWithOneLocation()]}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const repoHeader = await screen.findByRole('button', {name: /lorem/i});
      await userEvent.click(repoHeader);

      await waitFor(() => {
        // Three links. Two jobs, one repo name at the bottom.
        expect(screen.getAllByRole('link')).toHaveLength(3);
      });
    });

    it('initializes with all repos visible, if multiple options and no localStorage', async () => {
      render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider mocks={[buildWorkspaceQueryWithThreeLocations()]}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const loremHeader = await screen.findByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeVisible();
      const fooHeader = screen.getByRole('button', {name: /foo/i});
      expect(fooHeader).toBeVisible();
      const dunderHeader = screen.getByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeVisible();

      await userEvent.click(loremHeader);
      await userEvent.click(fooHeader);
      await userEvent.click(dunderHeader);

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
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider mocks={[buildWorkspaceQueryWithThreeLocations()]}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const fooHeader = await screen.findByRole('button', {name: /foo/i});
      await userEvent.click(fooHeader);

      // `foo@bar` is visible, and has four jobs. Plus one for repo link at bottom.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(5);
      });
    });

    it('initializes with all repo options, no matching `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(HIDDEN_REPO_KEYS, '["hello:world"]');

      render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider mocks={[buildWorkspaceQueryWithThreeLocations()]}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const loremHeader = await screen.findByRole('button', {name: /lorem/i});
      await waitFor(() => {
        expect(loremHeader).toBeVisible();
      });

      const fooHeader = screen.getByRole('button', {name: /foo/i});
      expect(fooHeader).toBeVisible();
      const dunderHeader = screen.getByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeVisible();

      await userEvent.click(loremHeader);
      await userEvent.click(fooHeader);
      await userEvent.click(dunderHeader);

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

      // `act` immediately because we are asserting null renders
      act(() => {
        render(
          <MemoryRouter initialEntries={['/runs']}>
            <MockedProvider mocks={[buildWorkspaceQueryWithThreeLocations()]}>
              <WorkspaceProvider>
                <LeftNavRepositorySection />
              </WorkspaceProvider>
            </MockedProvider>
          </MemoryRouter>,
        );
      });

      const loremHeader = screen.queryByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeNull();
      const fooHeader = screen.queryByRole('button', {name: /foo/i});
      expect(fooHeader).toBeNull();
      const dunderHeader = screen.queryByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeNull();

      // No linked jobs or repos. Everything is hidden.
      expect(screen.queryAllByRole('link')).toHaveLength(0);
    });

    it('initializes empty, then shows options when they are added', async () => {
      const ReloadableTest = () => {
        const {refetch} = React.useContext(WorkspaceContext);
        return (
          <>
            <button onClick={() => refetch()}>Refetch workspace</button>
            <LeftNavRepositorySection />
          </>
        );
      };

      const mocks = [
        buildWorkspaceQueryWithZeroLocations(),
        buildWorkspaceQueryWithThreeLocations(),
      ];

      render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider mocks={mocks}>
            <WorkspaceProvider>
              <ReloadableTest />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      // Zero repositories, so zero pipelines.
      expect(screen.queryAllByRole('link')).toHaveLength(0);

      const reloadButton = screen.getByRole('button', {name: /refetch workspace/i});
      await userEvent.click(reloadButton);

      const loremHeader = await screen.findByRole('button', {name: /lorem/i});
      await waitFor(() => {
        expect(loremHeader).toBeVisible();
      });

      const fooHeader = screen.getByRole('button', {name: /foo/i});
      expect(fooHeader).toBeVisible();
      const dunderHeader = screen.getByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeVisible();

      await userEvent.click(loremHeader);
      await userEvent.click(fooHeader);
      await userEvent.click(dunderHeader);

      // After repositories are added and expanded, all become visible.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(12);
      });
    });

    it('initializes with options, then shows empty if they are removed', async () => {
      const ReloadableTest = () => {
        const {refetch} = React.useContext(WorkspaceContext);
        return (
          <>
            <button onClick={() => refetch()}>Refetch workspace</button>
            <LeftNavRepositorySection />
          </>
        );
      };

      const mocks = [buildWorkspaceQueryWithOneLocation(), buildWorkspaceQueryWithZeroLocations()];

      render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider mocks={mocks}>
            <WorkspaceProvider>
              <ReloadableTest />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const loremHeader = await screen.findByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeVisible();
      await userEvent.click(loremHeader);

      // Three links: two jobs, one repo link at bottom.
      expect(screen.queryAllByRole('link')).toHaveLength(3);

      const reloadButton = screen.getByRole('button', {name: /refetch workspace/i});
      await userEvent.click(reloadButton);

      await waitFor(() => {
        // After repositories are removed, there are none displayed.
        expect(screen.queryAllByRole('link')).toHaveLength(0);
      });
    });
  });

  describe('Asset groups', () => {
    it('renders asset groups alongside jobs', async () => {
      render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider mocks={[buildWorkspaceQueryWithOneLocationAndAssetGroup()]}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const repoHeader = await screen.findByRole('button', {name: /lorem/i});
      await userEvent.click(repoHeader);

      await waitFor(() => {
        expect(
          screen.getByRole('link', {
            name: /my_pipeline/i,
          }),
        ).toBeVisible();
        expect(
          screen.getByRole('link', {
            name: /my_asset_group/i,
          }),
        ).toBeVisible();
      });
    });
  });
});
