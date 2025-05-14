import {MockedProvider} from '@apollo/client/testing';
import {render} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {mockViewportClientRect, restoreViewportClientRect} from '../../testing/mocking';
import {LeftNavRepositorySectionInner} from '../LeftNavRepositorySection';
import {
  abcLocationOption,
  buildInstigationStateQueryForLocation,
  fooBarOption,
  loremIpsumOption,
  uniqueOption,
} from '../__fixtures__/LeftNavRepositorySection.fixtures';

describe('LeftNavRepositorySection', () => {
  beforeEach(() => {
    mockViewportClientRect();
  });

  afterEach(() => {
    restoreViewportClientRect();
  });

  it('Correctly displays the current repository state', async () => {
    const user = userEvent.setup();
    const {findByRole} = render(
      <MemoryRouter initialEntries={['/locations/lorem@ipsum/etc']}>
        <MockedProvider mocks={[buildInstigationStateQueryForLocation('lorem')]}>
          <LeftNavRepositorySectionInner
            allRepos={[loremIpsumOption, fooBarOption, abcLocationOption]}
            visibleRepos={[loremIpsumOption]}
            toggleVisible={jest.fn()}
          />
        </MockedProvider>
      </MemoryRouter>,
    );

    const repoHeader = await findByRole('button', {name: /lorem@ipsum/i});
    await user.click(repoHeader);

    expect(await findByRole('link', {name: /my_pipeline/i})).toBeVisible();
  });

  it('initializes with first repo option', async () => {
    const {findByRole, findAllByRole} = render(
      <MemoryRouter initialEntries={['/runs']}>
        <MockedProvider mocks={[buildInstigationStateQueryForLocation('lorem')]}>
          <LeftNavRepositorySectionInner
            allRepos={[loremIpsumOption]}
            visibleRepos={[loremIpsumOption]}
            toggleVisible={jest.fn()}
          />
        </MockedProvider>
      </MemoryRouter>,
    );

    const repoHeader = await findByRole('button', {name: /lorem@ipsum/i});
    expect(repoHeader).toBeVisible();

    // Three links. Two jobs, one repo name at the bottom.
    expect(await findAllByRole('link')).toHaveLength(3);
  });

  it('renders asset groups alongside jobs', async () => {
    const user = userEvent.setup();

    const {findByRole} = render(
      <MemoryRouter initialEntries={['/runs']}>
        <MockedProvider mocks={[buildInstigationStateQueryForLocation('entry')]}>
          <LeftNavRepositorySectionInner
            allRepos={[uniqueOption]}
            visibleRepos={[uniqueOption]}
            toggleVisible={jest.fn()}
          />
        </MockedProvider>
      </MemoryRouter>,
    );

    const repoHeader = await findByRole('button', {name: /unique/i});
    await user.click(repoHeader);

    expect(await findByRole('link', {name: /my_pipeline/i})).toBeVisible();
    expect(await findByRole('link', {name: /my_asset_group/i})).toBeVisible();
  });
});
