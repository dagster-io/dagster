import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {TimezoneProvider, TimezoneStorageKey} from '../app/time/TimezoneContext';

import {useFormatDateTime} from './useFormatDateTime';

jest.mock('../app/time/browserTimezone', () => ({
  browserTimezone: jest.fn(() => 'Pacific/Honolulu'),
}));

const NYD_2023_CST = 1672552800000;

describe('useFormatDateTime', () => {
  interface Props {
    date: Date;
    options: Intl.DateTimeFormatOptions;
  }

  const Test: React.FC<Props> = ({date, options}) => {
    const formatDateTime = useFormatDateTime();
    return <div>{formatDateTime(date, options)}</div>;
  };

  afterEach(() => {
    window.localStorage.removeItem(TimezoneStorageKey);
  });

  describe('Automatic timezone', () => {
    // Timezone has not been set in localStorage, so it should be an `Automatic` timezone, and
    // we should end up using `browserTimezone()` as mocked above.
    it('renders with Pacific/Honolulu as the automatic timezone', async () => {
      render(
        <TimezoneProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{month: 'long', day: 'numeric', year: 'numeric', timeZoneName: 'short'}}
          />
        </TimezoneProvider>,
      );
      expect(screen.getByText(/December 31, 2022(.+) HST/)).toBeVisible();
    });

    it('renders both time and date', async () => {
      render(
        <TimezoneProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{
              month: 'long',
              day: 'numeric',
              year: 'numeric',
              hour: 'numeric',
              minute: 'numeric',
              timeZoneName: 'short',
            }}
          />
        </TimezoneProvider>,
      );
      expect(screen.getByText(/December 31, 2022(.+) 8:00 PM HST/)).toBeVisible();
    });

    it('can render just time', async () => {
      render(
        <TimezoneProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{
              hour: 'numeric',
              minute: 'numeric',
              timeZoneName: 'short',
            }}
          />
        </TimezoneProvider>,
      );
      expect(screen.getByText(/^8:00 PM HST/)).toBeVisible();
    });
  });

  // Set the timezone in localStorage, test that it is retrieved and used correctly
  // for the formatted string.
  describe('Saved timezone', () => {
    beforeEach(() => {
      window.localStorage.setItem(TimezoneStorageKey, 'Europe/Rome');
    });

    it('renders with Europe/Rome as the timezone', async () => {
      render(
        <TimezoneProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{month: 'long', day: 'numeric', year: 'numeric', timeZoneName: 'short'}}
          />
        </TimezoneProvider>,
      );
      expect(screen.getByText(/January 1, 2023(.+) GMT\+1/)).toBeVisible();
    });

    it('renders both time and date', async () => {
      render(
        <TimezoneProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{
              month: 'long',
              day: 'numeric',
              year: 'numeric',
              hour: 'numeric',
              minute: 'numeric',
              timeZoneName: 'short',
            }}
          />
        </TimezoneProvider>,
      );
      expect(screen.getByText(/January 1, 2023(.+) 7:00 AM GMT\+1/)).toBeVisible();
    });

    it('can render just time', async () => {
      render(
        <TimezoneProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{
              hour: 'numeric',
              minute: 'numeric',
              timeZoneName: 'short',
            }}
          />
        </TimezoneProvider>,
      );
      expect(screen.getByText(/^7:00 AM GMT\+1/)).toBeVisible();
    });
  });
});
