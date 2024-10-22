import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {InstigationTickStatus} from '../../graphql/types';
import {TickStatusTag} from '../../ticks/TickStatusTag';
import {TickTagFragment} from '../types/InstigationTick.types';

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

      render(<TickStatusTag tick={skippedTick} tickResultType="runs" />);

      const tag = screen.queryByText(/0 runs requested/i);
      expect(tag).toBeVisible();

      await userEvent.hover(tag as HTMLElement);
      await waitFor(() => {
        expect(screen.queryByText('lol skipped')).toBeVisible();
      });
    });

    it('renders info about requested run count if run keys', async () => {
      const skippedTick = {...tick, status: InstigationTickStatus.SKIPPED, runKeys: ['foo', 'bar']};

      render(<TickStatusTag tick={skippedTick} tickResultType="runs" />);

      const tag = screen.queryByText(/0 runs requested/i);
      expect(tag).toBeVisible();

      await userEvent.hover(tag as HTMLElement);
      await waitFor(() => {
        expect(screen.queryByText(/2 runs requested, but skipped/i)).toBeVisible();
      });
    });
  });
});
