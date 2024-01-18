import * as React from 'react';
import {act, render, screen} from '@testing-library/react';
import faker from 'faker';
import {MemoryRouter} from 'react-router-dom';

import {displayNameForAssetKey} from '../../asset-graph/Utils';
import {AssetKeyTagCollection} from '../AssetTagCollections';

describe('AssetKeyTagCollection', () => {
  const makeKeys = (count: number) => {
    return Array(count)
      .fill(null)
      .map((_) => ({path: [faker.random.word()]}));
  };

  it('renders individual tag if there is just one key', async () => {
    const key = makeKeys(1)[0]!;
    render(
      <MemoryRouter>
        <AssetKeyTagCollection assetKeys={[key]} useTags />
      </MemoryRouter>,
    );

    expect(screen.queryByText('1 asset')).toBeNull();
    expect(screen.queryByText(displayNameForAssetKey(key))).toBeDefined();
  });

  it('renders a "5 assets" tag if there are >1 key', async () => {
    const keys = makeKeys(5);
    // `act` because we're asserting a null state
    await act(async () => {
      render(
        <MemoryRouter>
          <AssetKeyTagCollection assetKeys={keys} useTags />
        </MemoryRouter>,
      );
    });

    expect(screen.queryByText('5 assets')).toBeDefined();
    expect(screen.queryByText(displayNameForAssetKey(keys[0]!))).toBeNull();
  });
});
