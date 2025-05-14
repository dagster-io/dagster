import {MockedProvider} from '@apollo/client/testing';
import {render, waitFor} from '@testing-library/react';
import {useContext} from 'react';

import {testId} from '../../testing/testId';
import {
  HIDDEN_REPO_KEYS,
  WorkspaceContext,
  WorkspaceProvider,
} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';
import {
  buildWorkspaceQueryWithOneLocation,
  buildWorkspaceQueryWithThreeLocations,
} from '../__fixtures__/LeftNavRepositorySection.fixtures';

describe('Repo option visibility', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  const Test = () => {
    const {visibleRepos, loading} = useContext(WorkspaceContext);
    return (
      <div data-testid={testId('target')}>
        {loading
          ? 'loading…'
          : visibleRepos
              .map((repo) => `${repo.repository.name}@${repo.repositoryLocation.name}`)
              .join(', ')}
      </div>
    );
  };

  it(`initializes with one repo if it's the only one, even though it's hidden`, async () => {
    window.localStorage.setItem(`:${HIDDEN_REPO_KEYS}`, `["lorem:ipsum"]`);

    const {findByTestId} = render(
      <MockedProvider mocks={[...buildWorkspaceQueryWithOneLocation()]}>
        <WorkspaceProvider>
          <Test />
        </WorkspaceProvider>
      </MockedProvider>,
    );

    const element = await findByTestId('target');
    expect(element).toHaveTextContent('loading…');
    await waitFor(async () => {
      expect(element).toHaveTextContent('lorem@ipsum');
    });
  });

  it('initializes with all repos visible, if multiple options and no localStorage', async () => {
    window.localStorage.removeItem(`:${HIDDEN_REPO_KEYS}`);

    const {findByTestId} = render(
      <MockedProvider mocks={[...buildWorkspaceQueryWithThreeLocations()]}>
        <WorkspaceProvider>
          <Test />
        </WorkspaceProvider>
      </MockedProvider>,
    );

    const element = await findByTestId('target');
    await waitFor(async () => {
      expect(element).toHaveTextContent('__repository__@abc_location, foo@bar, lorem@ipsum');
    });
  });

  it('initializes with correct repo option, if `HIDDEN_REPO_KEYS` localStorage', async () => {
    window.localStorage.setItem(
      `:${HIDDEN_REPO_KEYS}`,
      `["lorem:ipsum","${DUNDER_REPO_NAME}:abc_location"]`,
    );

    const {findByTestId} = render(
      <MockedProvider mocks={[...buildWorkspaceQueryWithThreeLocations()]}>
        <WorkspaceProvider>
          <Test />
        </WorkspaceProvider>
      </MockedProvider>,
    );

    const element = await findByTestId('target');
    await waitFor(async () => {
      expect(element).toHaveTextContent('foo@bar');
    });
  });

  it('initializes with all repo options, no matching `HIDDEN_REPO_KEYS` localStorage', async () => {
    window.localStorage.setItem(`:${HIDDEN_REPO_KEYS}`, '["hello:world"]');

    const {findByTestId} = render(
      <MockedProvider mocks={[...buildWorkspaceQueryWithThreeLocations()]}>
        <WorkspaceProvider>
          <Test />
        </WorkspaceProvider>
      </MockedProvider>,
    );

    const element = await findByTestId('target');
    await waitFor(async () => {
      expect(element).toHaveTextContent('__repository__@abc_location, foo@bar, lorem@ipsum');
    });
  });

  it('initializes empty, if all items in `HIDDEN_REPO_KEYS` localStorage', async () => {
    window.localStorage.setItem(
      `:${HIDDEN_REPO_KEYS}`,
      `["lorem:ipsum", "foo:bar", "${DUNDER_REPO_NAME}:abc_location"]`,
    );

    const {findByTestId} = render(
      <MockedProvider mocks={buildWorkspaceQueryWithThreeLocations()}>
        <WorkspaceProvider>
          <Test />
        </WorkspaceProvider>
      </MockedProvider>,
    );

    const element = await findByTestId('target');
    await waitFor(async () => {
      expect(element).not.toHaveTextContent('loading…');
    });

    expect(element).toHaveTextContent('');
  });
});
