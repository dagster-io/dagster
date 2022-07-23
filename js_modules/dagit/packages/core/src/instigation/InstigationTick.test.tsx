import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {InstigationTickStatus} from '../types/globalTypes';

import {TickTag} from './InstigationTick';
import {TickTagFragment} from './types/TickTagFragment';

describe('TickTag', () => {
  const tick: TickTagFragment = {
    __typename: 'InstigationTick',
    id: 'foobar',
    status: InstigationTickStatus.SUCCESS,
    timestamp: Date.now(),
    skipReason: 'lol skipped',
    runIds: [],
    runKeys: [],
    error: null,
  };

  describe('Skipped', () => {
    it('renders skip reason if no run keys', async () => {
      const skippedTick = {...tick, status: InstigationTickStatus.SKIPPED};

      render(<TickTag tick={skippedTick} />);

      const tag = screen.queryByText(/skipped/i);
      expect(tag).toBeVisible();

      userEvent.hover(tag as HTMLElement);
      await waitFor(() => {
        expect(screen.queryByText('lol skipped')).toBeVisible();
      });
    });

    it('renders info about requested run count if run keys', async () => {
      const skippedTick = {...tick, status: InstigationTickStatus.SKIPPED, runKeys: ['foo', 'bar']};

      render(<TickTag tick={skippedTick} />);

      const tag = screen.queryByText(/skipped/i);
      expect(tag).toBeVisible();

      userEvent.hover(tag as HTMLElement);
      await waitFor(() => {
        expect(screen.queryByText(/2 runs requested, but skipped/i)).toBeVisible();
      });
    });
  });
});
