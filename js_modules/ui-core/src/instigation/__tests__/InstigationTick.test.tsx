import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {InstigationTickStatus, buildInstigationTick} from '../../graphql/types';
import {TickStatusTag} from '../../ticks/TickStatusTag';

describe('TickTag', () => {
  const tickValues = {
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
      const user = userEvent.setup();
      const skippedTick = buildInstigationTick({
        ...tickValues,
        status: InstigationTickStatus.SKIPPED,
      });

      render(<TickStatusTag tick={skippedTick} tickResultType="runs" />);

      const tag = screen.queryByText('0 runs requested');
      expect(tag).toBeVisible();

      await user.hover(tag as HTMLElement);
      await waitFor(() => {
        expect(screen.queryByRole('tooltip', {name: /lol skipped/i})).toBeVisible();
      });
    });

    it('renders info about requested run count if run keys', async () => {
      const user = userEvent.setup();
      const skippedTick = buildInstigationTick({
        ...tickValues,
        status: InstigationTickStatus.SKIPPED,
        runKeys: ['foo', 'bar'],
      });

      render(<TickStatusTag tick={skippedTick} tickResultType="runs" />);

      const tag = screen.queryByText('0 runs requested');
      expect(tag).toBeVisible();

      await user.hover(tag as HTMLElement);
      await waitFor(() => {
        expect(
          screen.queryByRole('tooltip', {name: /2 runs requested, but skipped/i}),
        ).toBeVisible();
      });
    });
  });
});
