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
  });
});
