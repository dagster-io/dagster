import {formatDuration} from '../formatDuration';

describe('formatDuration', () => {
  describe('basic milliseconds formatting', () => {
    it('should format 0 milliseconds', () => {
      expect(formatDuration(0)).toEqual([{value: 0, unit: 'milliseconds'}]);
    });

    it('should format negative durations', () => {
      expect(formatDuration(-1000)).toEqual([{value: 0, unit: 'milliseconds'}]);
      expect(formatDuration(-5000)).toEqual([{value: 0, unit: 'milliseconds'}]);
    });

    it('should format milliseconds under 1000', () => {
      expect(formatDuration(1)).toEqual([{value: 1, unit: 'millisecond'}]);
      expect(formatDuration(500)).toEqual([{value: 500, unit: 'milliseconds'}]);
      expect(formatDuration(999)).toEqual([{value: 999, unit: 'milliseconds'}]);
    });

    it('should format seconds correctly', () => {
      expect(formatDuration(1000)).toEqual([{value: 1, unit: 'second'}]);
      expect(formatDuration(2000)).toEqual([{value: 2, unit: 'seconds'}]);
      expect(formatDuration(59000)).toEqual([{value: 59, unit: 'seconds'}]);
    });

    it('should format minutes correctly', () => {
      expect(formatDuration(60000)).toEqual([{value: 1, unit: 'minute'}]);
      expect(formatDuration(120000)).toEqual([{value: 2, unit: 'minutes'}]);
      expect(formatDuration(3540000)).toEqual([{value: 59, unit: 'minutes'}]);
    });

    it('should format hours correctly', () => {
      expect(formatDuration(3600000)).toEqual([{value: 1, unit: 'hour'}]);
      expect(formatDuration(7200000)).toEqual([{value: 2, unit: 'hours'}]);
      expect(formatDuration(82800000)).toEqual([{value: 23, unit: 'hours'}]);
    });

    it('should format days correctly', () => {
      expect(formatDuration(86400000)).toEqual([{value: 1, unit: 'day'}]);
      expect(formatDuration(172800000)).toEqual([{value: 48, unit: 'hours'}]);
      expect(formatDuration(604800000)).toEqual([{value: 7, unit: 'days'}]);
    });

    it('should format weeks correctly', () => {
      expect(formatDuration(604800000)).toEqual([{value: 7, unit: 'days'}]); // Should prefer days over 1 week
      expect(formatDuration(1209600000)).toEqual([{value: 14, unit: 'days'}]);
      expect(formatDuration(2419200000)).toEqual([{value: 28, unit: 'days'}]);
    });

    it('should format months correctly', () => {
      expect(formatDuration(2592000000)).toEqual([{value: 30, unit: 'days'}]); // Should prefer days
      expect(formatDuration(5184000000)).toEqual([{value: 60, unit: 'days'}]);
      expect(formatDuration(7776000000)).toEqual([{value: 90, unit: 'days'}]);
    });

    it('should format years correctly', () => {
      expect(formatDuration(31536000000)).toEqual([{value: 365, unit: 'days'}]); // Should prefer days
      expect(formatDuration(63072000000)).toEqual([{value: 24, unit: 'months'}]);
      expect(formatDuration(94608000000)).toEqual([{value: 36, unit: 'months'}]);
    });
  });

  describe('4-digit rule', () => {
    it('should avoid showing 1000+ of any unit', () => {
      // 1000 seconds should become minutes
      expect(formatDuration(1000000)).toEqual([{value: 16, unit: 'minutes'}]);

      // 1000 minutes should become hours
      expect(formatDuration(60000000)).toEqual([{value: 16, unit: 'hours'}]);

      // 1000 hours should become days
      expect(formatDuration(3600000000)).toEqual([{value: 41, unit: 'days'}]);
    });
  });

  describe('single significant digit (default)', () => {
    it('should show only the largest unit', () => {
      expect(formatDuration(1500)).toEqual([{value: 1, unit: 'second'}]);
      expect(formatDuration(65000)).toEqual([{value: 1, unit: 'minute'}]);
      expect(formatDuration(3665000)).toEqual([{value: 1, unit: 'hour'}]);
      expect(formatDuration(90000000)).toEqual([{value: 25, unit: 'hours'}]);
    });

    it('should round down to the nearest whole unit', () => {
      expect(formatDuration(1999)).toEqual([{value: 1, unit: 'second'}]);
      expect(formatDuration(119999)).toEqual([{value: 1, unit: 'minute'}]);
      expect(formatDuration(7199999)).toEqual([{value: 1, unit: 'hour'}]);
    });
  });

  describe('two significant digits', () => {
    it('should show two units when remainder exists', () => {
      expect(formatDuration(1500, {significantDigits: 2})).toEqual([
        {value: 1, unit: 'second'},
        {value: 500, unit: 'milliseconds'},
      ]);
      expect(formatDuration(65000, {significantDigits: 2})).toEqual([
        {value: 1, unit: 'minute'},
        {value: 5, unit: 'seconds'},
      ]);
      expect(formatDuration(3665000, {significantDigits: 2})).toEqual([
        {value: 1, unit: 'hour'},
        {value: 1, unit: 'minute'},
      ]);
      expect(formatDuration(90000000, {significantDigits: 2})).toEqual([
        {unit: 'hours', value: 25},
      ]);
    });

    it('should show only one unit when no remainder', () => {
      expect(formatDuration(1000, {significantDigits: 2})).toEqual([{value: 1, unit: 'second'}]);
      expect(formatDuration(60000, {significantDigits: 2})).toEqual([{value: 1, unit: 'minute'}]);
      expect(formatDuration(3600000, {significantDigits: 2})).toEqual([{value: 1, unit: 'hour'}]);
    });

    it('should handle complex durations', () => {
      expect(formatDuration(3723000, {significantDigits: 2})).toEqual([
        {value: 1, unit: 'hour'},
        {value: 2, unit: 'minutes'},
      ]);
      expect(formatDuration(93784000, {significantDigits: 2})).toEqual([
        {value: 26, unit: 'hours'},
        {value: 3, unit: 'minutes'},
      ]);
    });
  });

  describe('seconds input mode', () => {
    it('should convert seconds to appropriate units', () => {
      expect(formatDuration(1, {unit: 'seconds'})).toEqual([{value: 1, unit: 'second'}]);
      expect(formatDuration(60, {unit: 'seconds'})).toEqual([{value: 1, unit: 'minute'}]);
      expect(formatDuration(3600, {unit: 'seconds'})).toEqual([{value: 1, unit: 'hour'}]);
      expect(formatDuration(86400, {unit: 'seconds'})).toEqual([{value: 1, unit: 'day'}]);
    });

    it('should apply 4-digit rule to seconds input', () => {
      expect(formatDuration(1000, {unit: 'seconds'})).toEqual([{value: 16, unit: 'minutes'}]);
      expect(formatDuration(60000, {unit: 'seconds'})).toEqual([{value: 16, unit: 'hours'}]);
    });

    it('should work with two significant digits', () => {
      expect(formatDuration(1000, {unit: 'seconds', significantDigits: 2})).toEqual([
        {value: 16, unit: 'minutes'},
        {value: 40, unit: 'seconds'},
      ]);
      expect(formatDuration(3665, {unit: 'seconds', significantDigits: 2})).toEqual([
        {value: 1, unit: 'hour'},
        {value: 1, unit: 'minute'},
      ]);
      expect(formatDuration(90000, {unit: 'seconds', significantDigits: 2})).toEqual([
        {value: 25, unit: 'hours'},
      ]);
    });
  });

  describe('edge cases', () => {
    it('should handle very small values', () => {
      expect(formatDuration(0.5)).toEqual([{value: 0, unit: 'milliseconds'}]);
      expect(formatDuration(0.9)).toEqual([{value: 0, unit: 'milliseconds'}]);
    });

    it('should handle very large values', () => {
      expect(formatDuration(Number.MAX_SAFE_INTEGER)).toEqual([{value: 285616, unit: 'years'}]);
    });

    it('should handle fractional milliseconds by flooring', () => {
      expect(formatDuration(1500.7)).toEqual([{value: 1, unit: 'second'}]);
      expect(formatDuration(1500.7, {significantDigits: 2})).toEqual([
        {value: 1, unit: 'second'},
        {value: 500, unit: 'milliseconds'},
      ]);
    });

    it('should maintain singular/plural consistency', () => {
      expect(formatDuration(1000)).toEqual([{value: 1, unit: 'second'}]);
      expect(formatDuration(2000)).toEqual([{value: 2, unit: 'seconds'}]);
      expect(formatDuration(60000)).toEqual([{value: 1, unit: 'minute'}]);
      expect(formatDuration(120000)).toEqual([{value: 2, unit: 'minutes'}]);
      expect(formatDuration(3600000)).toEqual([{value: 1, unit: 'hour'}]);
      expect(formatDuration(7200000)).toEqual([{value: 2, unit: 'hours'}]);
    });
  });

  describe('real-world examples', () => {
    it('should format common durations correctly', () => {
      // API response time
      expect(formatDuration(247)).toEqual([{value: 247, unit: 'milliseconds'}]);

      // Video duration
      expect(formatDuration(215000)).toEqual([{value: 3, unit: 'minutes'}]);
      expect(formatDuration(215000, {significantDigits: 2})).toEqual([
        {value: 3, unit: 'minutes'},
        {value: 35, unit: 'seconds'},
      ]);

      // Upload time
      expect(formatDuration(45000)).toEqual([{value: 45, unit: 'seconds'}]);

      // Cache TTL
      expect(formatDuration(3600, {unit: 'seconds'})).toEqual([{value: 1, unit: 'hour'}]);

      // Session timeout
      expect(formatDuration(1800, {unit: 'seconds'})).toEqual([{value: 30, unit: 'minutes'}]);

      // Long-running job
      expect(formatDuration(7532000)).toEqual([{value: 2, unit: 'hours'}]);
      expect(formatDuration(7532000, {significantDigits: 2})).toEqual([
        {value: 2, unit: 'hours'},
        {value: 5, unit: 'minutes'},
      ]);
    });
  });
});
