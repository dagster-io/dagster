import {act, render, screen} from '@testing-library/react';
import faker from 'faker';
import {MemoryRouter} from 'react-router-dom';

import {AssetCheckTagCollection} from '../AssetTagCollections';

describe('AssetKeyTagCollection', () => {
  const makeKeys = (count: number) => {
    return Array(count)
      .fill(null)
      .map((_) => ({assetKey: {path: [faker.random.word()]}, name: faker.random.word()}));
  };

  it('renders individual tag if there is just one key', async () => {
    const key = makeKeys(1)[0]!;
    render(
      <MemoryRouter>
        <AssetCheckTagCollection assetChecks={[key]} useTags />
      </MemoryRouter>,
    );

    expect(screen.queryByText('1 asset')).toBeNull();
    expect(screen.queryByText(key.name)).toBeDefined();
  });

  it('renders a "5 assets" tag if there are >1 key', async () => {
    const keys = makeKeys(5);
    // `act` because we're asserting a null state
    await act(async () => {
      render(
        <MemoryRouter>
          <AssetCheckTagCollection assetChecks={keys} useTags />
        </MemoryRouter>,
      );
    });

    expect(screen.queryByText('5 assets')).toBeDefined();
    expect(screen.queryByText(keys.entries().next.name)).toBeNull();
  });
});
