import {humanCronString} from './humanCronString';

describe('humanCronString', () => {
  it('parses special strings correctly', () => {
    expect(humanCronString('@daily')).toBe('At 12:00 AM');
    expect(humanCronString('@weekly')).toBe('At 12:00 AM, only on Sunday');
    expect(humanCronString('@monthly')).toBe('At 12:00 AM, on day 1 of the month');
  });

  describe('Timezone', () => {
    it('shows timezone if provided, if cron specifies a time', () => {
      const timezone = 'America/Chicago';
      expect(humanCronString('@daily', timezone)).toBe('At 12:00 AM CDT');
      expect(humanCronString('@weekly', timezone)).toBe('At 12:00 AM CDT, only on Sunday');
      expect(humanCronString('@monthly', timezone)).toBe('At 12:00 AM CDT, on day 1 of the month');
      expect(humanCronString('0 23 ? * MON-FRI', timezone)).toBe(
        'At 11:00 PM CDT, Monday through Friday',
      );
      expect(humanCronString('0 23 * * *', timezone)).toBe('At 11:00 PM CDT');
    });

    it('does not show timezone even if provided, if cron does not specify a time', () => {
      const timezone = 'America/Chicago';
      expect(humanCronString('* * * * *', timezone)).toBe('Every minute');
      expect(humanCronString('* * * 6-8 *', timezone)).toBe('Every minute, June through August');
      expect(humanCronString('* * * * MON-FRI', timezone)).toBe(
        'Every minute, Monday through Friday',
      );
    });

    it('shows timezones on actual times, if cron is showing "X minutes..." or "X seconds..."', () => {
      const timezone = 'America/Chicago';
      expect(humanCronString('0 5 0/1 * * ?', timezone)).toBe('At 5 minutes past the hour');
      expect(humanCronString('30 * * 6-8 *', timezone)).toBe(
        'At 30 minutes past the hour, June through August',
      );
      expect(humanCronString('30 */5 * * * *', timezone)).toBe(
        'At 30 seconds past the minute, every 5 minutes',
      );
      expect(humanCronString('2,4-5 1 * * *', timezone)).toBe(
        'At 2 and 4 through 5 minutes past the hour, at 01:00 AM CDT',
      );
    });

    it('shows timezone in complex time cases', () => {
      const timezone = 'America/Chicago';
      expect(humanCronString('2-59/3 1,9,22 11-26 1-6 ?', timezone)).toBe(
        'Every 3 minutes, minutes 2 through 59 past the hour, at 01:00 AM CDT, 09:00 AM CDT, and 10:00 PM CDT, between day 11 and 26 of the month, January through June',
      );
      expect(humanCronString('12-50 0-10 6 * * * 2022', timezone)).toBe(
        'Seconds 12 through 50 past the minute, minutes 0 through 10 past the hour, at 06:00 AM CDT, only in 2022',
      );
    });

    it('shows timezone (UTC) if provided, if cron specifies a time', () => {
      const timezone = 'UTC';
      expect(humanCronString('@daily', timezone)).toBe('At 12:00 AM UTC');
      expect(humanCronString('@weekly', timezone)).toBe('At 12:00 AM UTC, only on Sunday');
      expect(humanCronString('@monthly', timezone)).toBe('At 12:00 AM UTC, on day 1 of the month');
      expect(humanCronString('0 23 ? * MON-FRI', timezone)).toBe(
        'At 11:00 PM UTC, Monday through Friday',
      );
      expect(humanCronString('0 23 * * *', timezone)).toBe('At 11:00 PM UTC');
    });

    describe('Invalid timezone', () => {
      beforeEach(() => {
        // `moment-timezone` will spew to the console, which is expected and not useful to us here.
        jest.spyOn(console, 'error').mockImplementation(() => {});
      });

      it('skips showing timezone if invalid', () => {
        const timezone = 'FooBar';
        expect(humanCronString('@daily', timezone)).toBe('At 12:00 AM');
        expect(humanCronString('@weekly', timezone)).toBe('At 12:00 AM, only on Sunday');
        expect(humanCronString('@monthly', timezone)).toBe('At 12:00 AM, on day 1 of the month');
        expect(humanCronString('0 23 ? * MON-FRI', timezone)).toBe(
          'At 11:00 PM, Monday through Friday',
        );
        expect(humanCronString('0 23 * * *', timezone)).toBe('At 11:00 PM');
      });
    });
  });

  describe('24-hour format', () => {
    const timezone = 'Europe/Berlin';
    let dateSpy;
    let languageGetter;

    beforeAll(() => {
      languageGetter = jest.spyOn(window.navigator, 'language', 'get');
      languageGetter.mockReturnValue('de-DE');
      dateSpy = jest.spyOn(Date.prototype, 'toLocaleTimeString');
      dateSpy.mockReturnValue('00:00:00');
    });

    afterAll(() => {
      jest.clearAllMocks();
    });

    it('shows 24h format if locale uses it, and shows timezone if provided, if cron specifies a time', () => {
      expect(humanCronString('@daily', timezone)).toBe('At 00:00 CEST');
      expect(humanCronString('@weekly', timezone)).toBe('At 00:00 CEST, only on Sunday');
      expect(humanCronString('@monthly', timezone)).toBe('At 00:00 CEST, on day 1 of the month');
      expect(humanCronString('0 23 ? * MON-FRI', timezone)).toBe(
        'At 23:00 CEST, Monday through Friday',
      );
      expect(humanCronString('0 23 * * *', timezone)).toBe('At 23:00 CEST');
    });

    it('shows 24h format if locale uses it, does not show timezone if not provided', () => {
      expect(humanCronString('@daily')).toBe('At 00:00');
      expect(humanCronString('@weekly')).toBe('At 00:00, only on Sunday');
      expect(humanCronString('@monthly')).toBe('At 00:00, on day 1 of the month');
      expect(humanCronString('0 23 ? * MON-FRI')).toBe('At 23:00, Monday through Friday');
      expect(humanCronString('0 23 * * *')).toBe('At 23:00');
    });

    it('shows timezone in complex time cases', () => {
      expect(humanCronString('2-59/3 1,9,22 11-26 1-6 ?', timezone)).toBe(
        'Every 3 minutes, minutes 2 through 59 past the hour, at 01:00 CEST, 09:00 CEST, and 22:00 CEST, between day 11 and 26 of the month, January through June',
      );
      expect(humanCronString('12-50 0-10 22 * * * 2022', timezone)).toBe(
        'Seconds 12 through 50 past the minute, minutes 0 through 10 past the hour, at 22:00 CEST, only in 2022',
      );
    });
  });
});
