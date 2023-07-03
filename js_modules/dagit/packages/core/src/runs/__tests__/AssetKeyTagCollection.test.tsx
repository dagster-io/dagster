import {act, render, screen} from '@testing-library/react';
import faker from 'faker';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {AssetKeyTagCollection} from '../AssetKeyTagCollection';

describe('AssetKeyTagCollection', () => {
  const makeKeys = (count: number) => {
    return Array(count)
      .fill(null)
      .map((_) => ({path: [faker.random.word()]}));
  };

  it('renders individual tags if <= 3', async () => {
    render(
      <MemoryRouter>
        <AssetKeyTagCollection assetKeys={makeKeys(3)} useTags />
      </MemoryRouter>,
    );

    const links = await screen.findAllByRole('link');
    expect(links).toHaveLength(3);

    expect(screen.queryByRole('button')).toBeNull();
  });

  it('renders single tag if > 3', async () => {
    // `act` because we're asserting a null state
    await act(async () => {
      render(
        <MemoryRouter>
          <AssetKeyTagCollection assetKeys={makeKeys(5)} useTags />
        </MemoryRouter>,
      );
    });

    const links = screen.queryByRole('link');
    expect(links).toBeNull();

    const button = screen.queryByRole('button') as HTMLButtonElement;
    expect(button.textContent).toBe('5 assets');
  });
});
