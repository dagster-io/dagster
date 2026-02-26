import {act, render, screen} from '@testing-library/react';

import {Delayed} from '../Delayed';

describe('Delayed', () => {
  beforeAll(() => {
    jest.useFakeTimers();
  });

  afterAll(() => {
    jest.useRealTimers();
  });

  it('delays rendering of loading state', async () => {
    const delay = 5000;
    const checkpoint = 2000;

    render(<Delayed delayMsec={delay}>Hey kid I&apos;m a computer</Delayed>);

    // Initially empty
    expect(screen.queryByText(/hey kid/i)).toBeNull();

    // Run to checkpoint
    act(() => jest.advanceTimersByTime(checkpoint));

    // Still empty
    expect(screen.queryByText(/hey kid/i)).toBeNull();

    // Run to completion
    act(() => jest.advanceTimersByTime(delay - checkpoint));

    // Delay complete, loading text is now visible
    expect(await screen.findByText(/hey kid/i)).toBeVisible();
  });
});
