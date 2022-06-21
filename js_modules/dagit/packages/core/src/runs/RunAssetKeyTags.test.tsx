import {act, render, screen} from '@testing-library/react';
import faker from 'faker';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {RunAssetKeyTags} from './RunAssetKeyTags';

describe('RunAssetKeyTags', () => {
  const makeKeys = (count: number) => {
    return Array(count)
      .fill(null)
      .map((_) => ({path: [faker.random.word()]}));
  };

  it('renders individual tags if <= 3', async () => {
    await act(async () => {
      render(
        <TestProvider>
          <RunAssetKeyTags assetKeys={makeKeys(3)} clickableTags />
        </TestProvider>,
      );
    });

    const links = screen.queryAllByRole('link');
    expect(links).toHaveLength(3);

    expect(screen.queryByRole('button')).toBeNull();
  });

  it('renders single tag if > 3', async () => {
    await act(async () => {
      render(
        <TestProvider>
          <RunAssetKeyTags assetKeys={makeKeys(5)} clickableTags />
        </TestProvider>,
      );
    });

    const links = screen.queryByRole('link');
    expect(links).toBeNull();

    const button = screen.queryByRole('button') as HTMLButtonElement;
    expect(button.textContent).toBe('5 assets');
  });
});
