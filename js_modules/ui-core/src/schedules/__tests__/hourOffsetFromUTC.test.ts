import {hourOffsetFromUTC} from '../hourOffsetFromUTC';

describe('hourOffsetFromUTC', () => {
  const JUL_1_2024_9_AM_CDT = new Date('2024-07-01T15:00:00.000Z');
  const NOV_5_2024_9_AM_CST = new Date('2024-11-05T15:00:00.000Z');

  beforeAll(() => {
    jest.useFakeTimers();
  });

  afterAll(() => {
    jest.useRealTimers();
  });

  describe('Standard time in Northern Hemisphere', () => {
    beforeEach(() => {
      jest.setSystemTime(NOV_5_2024_9_AM_CST);
    });

    it('returns the offset for a given timezone', () => {
      // Timezones with DST in Northern Hemisphere:
      expect(hourOffsetFromUTC('America/New_York')).toBe(-5);
      expect(hourOffsetFromUTC('America/Los_Angeles')).toBe(-8);
      expect(hourOffsetFromUTC('America/St_Johns')).toBe(-3.5);

      // Timezones without DST:
      expect(hourOffsetFromUTC('UTC')).toBe(0);
      expect(hourOffsetFromUTC('Europe/Berlin')).toBe(1);
      expect(hourOffsetFromUTC('Asia/Tokyo')).toBe(9);
      expect(hourOffsetFromUTC('Asia/Shanghai')).toBe(8);

      // Timezones with DST in Southern Hemisphere:
      expect(hourOffsetFromUTC('America/Santiago')).toBe(-3);
      expect(hourOffsetFromUTC('Australia/Adelaide')).toBe(10.5);
    });
  });

  describe('Daylight savings time in Northern Hemisphere', () => {
    beforeEach(() => {
      jest.setSystemTime(JUL_1_2024_9_AM_CDT);
    });

    it('returns the offset for a given timezone', () => {
      // Timezones with DST in Northern Hemisphere:
      expect(hourOffsetFromUTC('America/New_York')).toBe(-4);
      expect(hourOffsetFromUTC('America/Los_Angeles')).toBe(-7);
      expect(hourOffsetFromUTC('America/St_Johns')).toBe(-2.5);
      expect(hourOffsetFromUTC('Europe/Berlin')).toBe(2);

      // Timezones without DST:
      expect(hourOffsetFromUTC('UTC')).toBe(0);
      expect(hourOffsetFromUTC('Asia/Tokyo')).toBe(9);
      expect(hourOffsetFromUTC('Asia/Shanghai')).toBe(8);

      // Timezones with DST in Southern Hemisphere:
      expect(hourOffsetFromUTC('America/Santiago')).toBe(-4);
      expect(hourOffsetFromUTC('Australia/Adelaide')).toBe(9.5);
    });
  });
});
