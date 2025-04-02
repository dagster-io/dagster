import {MockedProvider} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {useContext} from 'react';
import {MemoryRouter} from 'react-router-dom';

import {__resetForJest} from '../../search/useIndexedDBCachedQuery';
import {mockViewportClientRect, restoreViewportClientRect} from '../../testing/mocking';
import {
  HIDDEN_REPO_KEYS,
  WorkspaceContext,
  WorkspaceProvider,
} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';
import {LeftNavRepositorySection} from '../LeftNavRepositorySection';
import {
  buildInstigationStateQueryForLocation,
  buildWorkspaceQueryWithOneLocation,
  buildWorkspaceQueryWithOneLocationAndAssetGroup,
  buildWorkspaceQueryWithThreeLocations,
  buildWorkspaceQueryWithZeroLocations,
} from '../__fixtures__/LeftNavRepositorySection.fixtures';

describe('Repository options', () => {
  const locationOne = 'ipsum';
  const repoOne = 'lorem';

  beforeEach(() => {
    window.localStorage.clear();
    mockViewportClientRect();
  });

  afterEach(() => {
    restoreViewportClientRect();
    window.localStorage.clear();
    __resetForJest();
    jest.resetModules();
    jest.resetAllMocks();
  });

  it('Correctly displays the current repository state', async () => {
    window.localStorage.removeItem(`:${HIDDEN_REPO_KEYS}`);
    const user = userEvent.setup();
    const {findByRole} = render(
      <MemoryRouter initialEntries={['/locations/foo@bar/etc']}>
        <MockedProvider
          mocks={[
            ...buildWorkspaceQueryWithOneLocation(),
            buildInstigationStateQueryForLocation('lorem'),
          ]}
        >
          <WorkspaceProvider>
            <LeftNavRepositorySection />
          </WorkspaceProvider>
        </MockedProvider>
      </MemoryRouter>,
    );

    const repoHeader = await findByRole('button', {name: /lorem/i});
    await user.click(repoHeader);

    expect(await findByRole('link', {name: /my_pipeline/i})).toBeVisible();
  });

  describe('localStorage', () => {
    it('initializes with first repo option, if one option and no localStorage', async () => {
      window.localStorage.removeItem(`:${HIDDEN_REPO_KEYS}`);
      const user = userEvent.setup();
      const {findByRole, findAllByRole} = render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithOneLocation(),
              buildInstigationStateQueryForLocation('lorem'),
            ]}
          >
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const repoHeader = await findByRole('button', {name: /lorem/i});
      await user.click(repoHeader);

      // Three links. Two jobs, one repo name at the bottom.
      expect(await findAllByRole('link')).toHaveLength(3);
    });

    it(`initializes with one repo if it's the only one, even though it's hidden`, async () => {
      window.localStorage.setItem(`:${HIDDEN_REPO_KEYS}`, `["${repoOne}:${locationOne}"]`);
      const user = userEvent.setup();
      const {findByRole, findAllByRole} = render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithOneLocation(),
              buildInstigationStateQueryForLocation('lorem'),
            ]}
          >
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const repoHeader = await findByRole('button', {name: /lorem/i});
      await user.click(repoHeader);

      expect(await findAllByRole('link')).toHaveLength(3);
    });

    it('initializes with all repos visible, if multiple options and no localStorage', async () => {
      window.localStorage.removeItem(`:${HIDDEN_REPO_KEYS}`);
      const {findByRole} = render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithThreeLocations(),
              buildInstigationStateQueryForLocation('lorem'),
            ]}
          >
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const loremHeader = await findByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeVisible();
      const fooHeader = await findByRole('button', {name: /foo/i});
      expect(fooHeader).toBeVisible();
      const dunderHeader = await findByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeVisible();
    });

    it('initializes with correct repo option, if `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(
        `:${HIDDEN_REPO_KEYS}`,
        `["lorem:ipsum","${DUNDER_REPO_NAME}:abc_location"]`,
      );

      const user = userEvent.setup();
      const {findByRole, findAllByRole} = render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithThreeLocations(),
              buildInstigationStateQueryForLocation('foo'),
            ]}
          >
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const fooHeader = await findByRole('button', {name: /foo/i});
      await user.click(fooHeader);

      // `foo@bar` is visible, and has four jobs. Plus one for repo link at bottom.
      expect(await findAllByRole('link')).toHaveLength(5);
    });

    it('initializes with all repo options, no matching `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(`:${HIDDEN_REPO_KEYS}`, '["hello:world"]');

      const {findByRole} = render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithThreeLocations(),
              buildInstigationStateQueryForLocation('lorem'),
              buildInstigationStateQueryForLocation('foo'),
              buildInstigationStateQueryForLocation('abc_location_repo_id'),
            ]}
          >
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const loremHeader = await findByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeVisible();
      const fooHeader = await findByRole('button', {name: /foo/i});
      expect(fooHeader).toBeVisible();
      const dunderHeader = await findByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeVisible();
    });

    it('initializes empty, if all items in `HIDDEN_REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(
        `:${HIDDEN_REPO_KEYS}`,
        `["lorem:ipsum", "foo:bar", "${DUNDER_REPO_NAME}:abc_location"]`,
      );

      const {findByText, queryByRole, queryAllByRole} = render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider mocks={buildWorkspaceQueryWithThreeLocations()}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      expect(await findByText(/select a code location to see a list of jobs/i)).toBeVisible();
      const loremHeader = queryByRole('button', {name: /lorem/i});
      expect(loremHeader).toBeNull();
      const fooHeader = queryByRole('button', {name: /foo/i});
      expect(fooHeader).toBeNull();
      const dunderHeader = queryByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeNull();

      // No linked jobs or repos. Everything is hidden.
      expect(queryAllByRole('link')).toHaveLength(0);
    });

    // eslint-disable-next-line jest/no-disabled-tests
    it.skip('initializes empty, then shows options when they are added', async () => {
      const ReloadableTest = () => {
        const {refetch} = useContext(WorkspaceContext);
        return (
          <>
            <button onClick={() => refetch()}>Refetch workspace</button>
            <LeftNavRepositorySection />
          </>
        );
      };

      const mocks = [
        ...buildWorkspaceQueryWithZeroLocations(),
        ...buildWorkspaceQueryWithThreeLocations(),
      ];

      await act(() =>
        render(
          <MemoryRouter initialEntries={['/runs']}>
            <MockedProvider mocks={mocks}>
              <WorkspaceProvider>
                <ReloadableTest />
              </WorkspaceProvider>
            </MockedProvider>
          </MemoryRouter>,
        ),
      );

      // Zero repositories, so zero pipelines.
      expect(screen.queryAllByRole('link')).toHaveLength(0);

      const reloadButton = screen.getByRole('button', {name: /refetch workspace/i});
      await userEvent.click(reloadButton);

      const loremHeader = await waitFor(() => screen.findByRole('button', {name: /lorem/i}));
      await waitFor(() => {
        expect(loremHeader).toBeVisible();
      });

      const fooHeader = screen.getByRole('button', {name: /foo/i});
      expect(fooHeader).toBeVisible();
      const dunderHeader = screen.getByRole('button', {name: /abc_location/i});
      expect(dunderHeader).toBeVisible();

      await act(async () => {
        await userEvent.click(loremHeader);
        await userEvent.click(fooHeader);
        await userEvent.click(dunderHeader);
      });

      // After repositories are added and expanded, all become visible.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(12);
      });
    });

    // eslint-disable-next-line jest/no-disabled-tests
    it.skip('initializes with options, then shows empty if they are removed', async () => {
      const ReloadableTest = () => {
        const {refetch} = useContext(WorkspaceContext);
        return (
          <>
            <button onClick={() => refetch()}>Refetch workspace</button>
            <LeftNavRepositorySection />
          </>
        );
      };

      const mocks = [
        ...buildWorkspaceQueryWithOneLocation(),
        ...buildWorkspaceQueryWithZeroLocations(),
      ];

      await act(() =>
        render(
          <MemoryRouter initialEntries={['/runs']}>
            <MockedProvider mocks={mocks}>
              <WorkspaceProvider>
                <ReloadableTest />
              </WorkspaceProvider>
            </MockedProvider>
          </MemoryRouter>,
        ),
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
      window.localStorage.removeItem(`:${HIDDEN_REPO_KEYS}`);
      const user = userEvent.setup();
      const {findByRole} = render(
        <MemoryRouter initialEntries={['/runs']}>
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithOneLocationAndAssetGroup(),
              buildInstigationStateQueryForLocation('entry'),
            ]}
          >
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      const repoHeader = await findByRole('button', {name: /unique/i});
      await user.click(repoHeader);

      expect(await findByRole('link', {name: /my_pipeline/i})).toBeVisible();
      expect(await findByRole('link', {name: /my_asset_group/i})).toBeVisible();
    });
  });
});
