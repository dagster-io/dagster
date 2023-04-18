import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {HourCycleKey, TimeProvider, TimezoneStorageKey} from '../../app/time/TimeContext';
import {useFormatDateTime} from '../useFormatDateTime';

jest.mock('../../app/time/browserTimezone', () => ({
  browserTimezone: jest.fn(() => 'Pacific/Honolulu'),
}));

const NYD_2023_CST = 1672552800000;

describe('useFormatDateTime', () => {
  interface Props {
    date: Date;
    options: Intl.DateTimeFormatOptions;
    language?: string;
  }

  const Test: React.FC<Props> = ({date, options, language}) => {
    const formatDateTime = useFormatDateTime();
    return <div>{formatDateTime(date, options, language)}</div>;
  };

  afterEach(() => {
    window.localStorage.removeItem(TimezoneStorageKey);
  });

  describe('Automatic timezone', () => {
    // Timezone has not been set in localStorage, so it should be an `Automatic` timezone, and
    // we should end up using `browserTimezone()` as mocked above.
    it('renders with Pacific/Honolulu as the automatic timezone', async () => {
      render(
        <TimeProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{month: 'long', day: 'numeric', year: 'numeric', timeZoneName: 'short'}}
          />
        </TimeProvider>,
      );
      expect(screen.getByText(/December 31, 2022(.+) HST/)).toBeVisible();
    });

    it('renders both time and date', async () => {
      render(
        <TimeProvider>
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
        </TimeProvider>,
      );
      expect(screen.getByText(/December 31, 2022(.+) 8:00 PM HST/)).toBeVisible();
    });

    it('can render just time', async () => {
      render(
        <TimeProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{
              hour: 'numeric',
              minute: 'numeric',
              timeZoneName: 'short',
            }}
          />
        </TimeProvider>,
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
        <TimeProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{month: 'long', day: 'numeric', year: 'numeric', timeZoneName: 'short'}}
          />
        </TimeProvider>,
      );
      expect(screen.getByText(/January 1, 2023(.+) GMT\+1/)).toBeVisible();
    });

    it('renders both time and date', async () => {
      render(
        <TimeProvider>
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
        </TimeProvider>,
      );
      expect(screen.getByText(/January 1, 2023(.+) 7:00 AM GMT\+1/)).toBeVisible();
    });

    it('can render just time', async () => {
      render(
        <TimeProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{
              hour: 'numeric',
              minute: 'numeric',
              timeZoneName: 'short',
            }}
          />
        </TimeProvider>,
      );
      expect(screen.getByText(/^7:00 AM GMT\+1/)).toBeVisible();
    });
  });

  describe('Saved hour cycle', () => {
    describe('Automatic', () => {
      beforeEach(() => {
        window.localStorage.removeItem(HourCycleKey);
      });

      afterEach(() => {
        jest.clearAllMocks();
      });

      it('renders with 12-hour cycle for en-US', async () => {
        const languageGetter = jest.spyOn(window.navigator, 'language', 'get');
        languageGetter.mockReturnValueOnce('en-US');
        render(
          <TimeProvider>
            <Test
              date={new Date(NYD_2023_CST)}
              options={{dateStyle: 'short', timeStyle: 'short'}}
            />
          </TimeProvider>,
        );
        expect(screen.getByText(/12\/31\/22, 8:00 PM/)).toBeVisible();
      });

      it('renders with 24-hour cycle for de-DE', async () => {
        const languageGetter = jest.spyOn(window.navigator, 'language', 'get');
        languageGetter.mockReturnValueOnce('de-DE');
        render(
          <TimeProvider>
            <Test
              date={new Date(NYD_2023_CST)}
              options={{dateStyle: 'short', timeStyle: 'short'}}
            />
          </TimeProvider>,
        );
        expect(screen.getByText(/31\.12\.22, 20:00/)).toBeVisible();
      });
    });

    describe('12-hour', () => {
      beforeEach(() => {
        window.localStorage.setItem(HourCycleKey, 'h12');
      });

      it('renders with 12-hour cycle', async () => {
        render(
          <TimeProvider>
            <Test
              date={new Date(NYD_2023_CST)}
              options={{dateStyle: 'short', timeStyle: 'short'}}
            />
          </TimeProvider>,
        );
        expect(screen.getByText(/12\/31\/22, 8:00 PM/)).toBeVisible();
      });
    });

    describe('24-hour', () => {
      beforeEach(() => {
        window.localStorage.setItem(HourCycleKey, 'h23');
      });

      it('renders with 24-hour cycle', async () => {
        render(
          <TimeProvider>
            <Test
              date={new Date(NYD_2023_CST)}
              options={{dateStyle: 'short', timeStyle: 'short'}}
            />
          </TimeProvider>,
        );
        expect(screen.getByText(/12\/31\/22, 20:00/)).toBeVisible();
      });
    });
  });

  describe('Manual language setting', () => {
    beforeEach(() => {
      const languageGetter = jest.spyOn(window.navigator, 'language', 'get');
      languageGetter.mockReturnValue('de-DE');
    });

    afterEach(() => {
      jest.clearAllMocks();
    });

    it('uses navigator.language by default (de-DE)', () => {
      render(
        <TimeProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{month: 'short', day: 'numeric', year: 'numeric', timeZoneName: 'short'}}
          />
        </TimeProvider>,
      );
      expect(screen.getByText(/31\. Dez\. 2022, GMT-10/)).toBeVisible();
    });

    it('uses allows passing a custom language (pt-PT overrides de-DE)', () => {
      render(
        <TimeProvider>
          <Test
            date={new Date(NYD_2023_CST)}
            options={{month: 'short', day: 'numeric', year: 'numeric', timeZoneName: 'short'}}
            language="pt-PT"
          />
        </TimeProvider>,
      );
      expect(screen.getByText(/31\/12\/2022, GMT-10/)).toBeVisible();
    });
  });
});
