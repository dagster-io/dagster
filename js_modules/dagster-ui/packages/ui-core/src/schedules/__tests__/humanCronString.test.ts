import {humanCronString} from '../humanCronString';

describe('humanCronString', () => {
  it('parses special strings correctly', () => {
    expect(humanCronString('@daily')).toBe('At 12:00 AM');
    expect(humanCronString('@weekly')).toBe('At 12:00 AM, only on Sunday');
    expect(humanCronString('@monthly')).toBe('At 12:00 AM, on day 1 of the month');
  });

  // Arizona does not use daylight savings.
  describe('Timezone', () => {
    it('shows timezone if provided, if cron specifies a time', () => {
      const timezone = 'America/Phoenix';
      const timezoneConfig = {longTimezoneName: timezone};
      expect(humanCronString('@daily', timezoneConfig)).toBe('At 12:00 AM MST');
      expect(humanCronString('@weekly', timezoneConfig)).toBe('At 12:00 AM MST, only on Sunday');
      expect(humanCronString('@monthly', timezoneConfig)).toBe(
        'At 12:00 AM MST, on day 1 of the month',
      );
      expect(humanCronString('0 23 ? * MON-FRI', timezoneConfig)).toBe(
        'At 11:00 PM MST, Monday through Friday',
      );
      expect(humanCronString('0 23 * * *', timezoneConfig)).toBe('At 11:00 PM MST');
    });

    it('does not show timezone even if provided, if cron does not specify a time', () => {
      const timezone = 'America/Phoenix';
      const timezoneConfig = {longTimezoneName: timezone};
      expect(humanCronString('* * * * *', timezoneConfig)).toBe('Every minute');
      expect(humanCronString('* * * 6-8 *', timezoneConfig)).toBe(
        'Every minute, June through August',
      );
      expect(humanCronString('* * * * MON-FRI', timezoneConfig)).toBe(
        'Every minute, Monday through Friday',
      );
    });

    it('shows timezones on actual times, if cron is showing "X minutes..." or "X seconds..."', () => {
      const timezone = 'America/Phoenix';
      const timezoneConfig = {longTimezoneName: timezone};
      expect(humanCronString('0 5 0/1 * * ?', timezoneConfig)).toBe('At 5 minutes past the hour');
      expect(humanCronString('30 * * 6-8 *', timezoneConfig)).toBe(
        'At 30 minutes past the hour, June through August',
      );
      expect(humanCronString('30 */5 * * * *', timezoneConfig)).toBe(
        'At 30 seconds past the minute, every 5 minutes',
      );
      expect(humanCronString('2,4-5 1 * * *', timezoneConfig)).toBe(
        'At 2 and 4 through 5 minutes past the hour, at 01:00 AM MST',
      );
    });

    it('shows timezone in complex time cases', () => {
      const timezone = 'America/Phoenix';
      const timezoneConfig = {longTimezoneName: timezone};
      expect(humanCronString('2-59/3 1,9,22 11-26 1-6 ?', timezoneConfig)).toBe(
        'Every 3 minutes, minutes 2 through 59 past the hour, at 01:00 AM MST, 09:00 AM MST, and 10:00 PM MST, between day 11 and 26 of the month, January through June',
      );
      expect(humanCronString('12-50 0-10 6 * * * 2022', timezoneConfig)).toBe(
        'Seconds 12 through 50 past the minute, minutes 0 through 10 past the hour, at 06:00 AM MST, only in 2022',
      );
    });

    it('shows timezone (UTC) if provided, if cron specifies a time', () => {
      const timezone = 'UTC';
      const timezoneConfig = {longTimezoneName: timezone};
      expect(humanCronString('@daily', timezoneConfig)).toBe('At 12:00 AM UTC');
      expect(humanCronString('@weekly', timezoneConfig)).toBe('At 12:00 AM UTC, only on Sunday');
      expect(humanCronString('@monthly', timezoneConfig)).toBe(
        'At 12:00 AM UTC, on day 1 of the month',
      );
      expect(humanCronString('0 23 ? * MON-FRI', timezoneConfig)).toBe(
        'At 11:00 PM UTC, Monday through Friday',
      );
      expect(humanCronString('0 23 * * *', timezoneConfig)).toBe('At 11:00 PM UTC');
    });

    describe('Invalid timezone', () => {
      it('skips showing timezone if invalid', () => {
        const timezone = 'FooBar';
        const timezoneConfig = {longTimezoneName: timezone};
        expect(humanCronString('@daily', timezoneConfig)).toBe('At 12:00 AM');
        expect(humanCronString('@weekly', timezoneConfig)).toBe('At 12:00 AM, only on Sunday');
        expect(humanCronString('@monthly', timezoneConfig)).toBe(
          'At 12:00 AM, on day 1 of the month',
        );
        expect(humanCronString('0 23 ? * MON-FRI', timezoneConfig)).toBe(
          'At 11:00 PM, Monday through Friday',
        );
        expect(humanCronString('0 23 * * *', timezoneConfig)).toBe('At 11:00 PM');
      });
    });

    describe('With timezone offset', () => {
      it('applies timezone offset for westward timezones, if provided', () => {
        const userTimezone = 'America/Los_Angeles';
        const timezoneConfig = {
          longTimezoneName: userTimezone,
          tzOffset: -1, // Difference between MST and PST
        };
        expect(humanCronString('@daily', timezoneConfig)).toBe('At 11:00 PM PST');
      });

      it('applies timezone offset for eastward timezones, if provided', () => {
        const userTimezone = 'America/St_Johns';
        const timezoneConfig = {
          longTimezoneName: userTimezone,
          tzOffset: 4.5, // Difference between Newfoundland standard time and PST
        };
        expect(humanCronString('@daily', timezoneConfig)).toBe('At 04:30 AM GMT-3:30');
      });

      it('applies timezone offset for timezones across the dateline, if provided', () => {
        const userTimezone = 'Asia/Tokyo';
        const timezoneConfig = {
          longTimezoneName: userTimezone,
          tzOffset: 16, // Difference between Tokyo and PST
        };
        expect(humanCronString('@daily', timezoneConfig)).toBe('At 04:00 PM GMT+9');
      });

      it('applies timezone offset for weekly cron schedule for timezones across the dateline', () => {
        const userTimezone = 'Asia/Tokyo';
        const timezoneConfig = {
          longTimezoneName: userTimezone,
          tzOffset: 16, // Difference between Tokyo and PST
        };

        // This is wrong! It should be "At 04:00 PM GMT+9, only on Monday". Keeping the test
        // here so that if we're able to upgrade cronstrue, a failure here tells us that it's fixed.
        // https://github.com/bradymholt/cRonstrue/issues/313
        expect(humanCronString('@weekly', timezoneConfig)).toBe(
          'At 04:00 PM GMT+9, only on Sunday',
        );
      });
    });
  });

  describe('24-hour format', () => {
    // Thailand uses 24h format and does not use daylight savings.
    const timezone = 'Asia/Bangkok';
    let dateSpy;
    let languageGetter;

    beforeAll(() => {
      languageGetter = jest.spyOn(window.navigator, 'language', 'get');
      languageGetter.mockReturnValue('th-TH');
      dateSpy = jest.spyOn(Date.prototype, 'toLocaleTimeString');
      dateSpy.mockReturnValue('00:00:00');
    });

    afterAll(() => {
      jest.clearAllMocks();
      jest.restoreAllMocks();
    });

    it('shows 24h format if locale uses it, and shows timezone if provided, if cron specifies a time', () => {
      const timezoneConfig = {longTimezoneName: timezone};
      expect(humanCronString('@daily', timezoneConfig)).toBe('At 00:00 GMT+7');
      expect(humanCronString('@weekly', timezoneConfig)).toBe('At 00:00 GMT+7, only on Sunday');
      expect(humanCronString('@monthly', timezoneConfig)).toBe(
        'At 00:00 GMT+7, on day 1 of the month',
      );
      expect(humanCronString('0 23 ? * MON-FRI', timezoneConfig)).toBe(
        'At 23:00 GMT+7, Monday through Friday',
      );
      expect(humanCronString('0 23 * * *', timezoneConfig)).toBe('At 23:00 GMT+7');
    });

    it('shows 24h format if locale uses it, does not show timezone if not provided', () => {
      expect(humanCronString('@daily')).toBe('At 00:00');
      expect(humanCronString('@weekly')).toBe('At 00:00, only on Sunday');
      expect(humanCronString('@monthly')).toBe('At 00:00, on day 1 of the month');
      expect(humanCronString('0 23 ? * MON-FRI')).toBe('At 23:00, Monday through Friday');
      expect(humanCronString('0 23 * * *')).toBe('At 23:00');
    });

    it('shows timezone in complex time cases', () => {
      const timezoneConfig = {longTimezoneName: timezone};
      expect(humanCronString('2-59/3 1,9,22 11-26 1-6 ?', timezoneConfig)).toBe(
        'Every 3 minutes, minutes 2 through 59 past the hour, at 01:00 GMT+7, 09:00 GMT+7, and 22:00 GMT+7, between day 11 and 26 of the month, January through June',
      );
      expect(humanCronString('12-50 0-10 22 * * * 2022', timezoneConfig)).toBe(
        'Seconds 12 through 50 past the minute, minutes 0 through 10 past the hour, at 22:00 GMT+7, only in 2022',
      );
    });
  });

  describe('Cron union', () => {
    it('handles a single-item union of cron strings, with timezone', () => {
      const timezone = 'America/Phoenix';
      const timezoneConfig = {longTimezoneName: timezone};
      expect(humanCronString("['2,4-5 1 * * *']", timezoneConfig)).toBe(
        'At 2 and 4 through 5 minutes past the hour, at 01:00 AM MST',
      );
    });

    it('handles a union of cron strings', () => {
      expect(humanCronString("['0 2 * * FRI-SAT', '0 2,8 * * MON,FRI', '*/30 9 * * SUN']")).toBe(
        'At 02:00 AM, Friday through Saturday; At 02:00 AM and 08:00 AM, only on Monday and Friday; Every 30 minutes, between 09:00 AM and 09:59 AM, only on Sunday',
      );
      expect(humanCronString("['* * * 6-8 *', '* * * * MON-FRI']")).toBe(
        'Every minute, June through August; Every minute, Monday through Friday',
      );
    });

    it('handles a union of special cron strings', () => {
      expect(humanCronString("['@daily', '@weekly']")).toBe(
        'At 12:00 AM; At 12:00 AM, only on Sunday',
      );
      expect(humanCronString("['@daily', '0 23 * * *']")).toBe('At 12:00 AM; At 11:00 PM');
    });

    it('handles a union of cron strings, with timezone', () => {
      const timezone = 'America/Phoenix';
      const timezoneConfig = {longTimezoneName: timezone};
      expect(humanCronString("['0 5 0/1 * * ?', '0 23 ? * MON-FRI']", timezoneConfig)).toBe(
        'At 5 minutes past the hour; At 11:00 PM MST, Monday through Friday',
      );
    });
  });
});
