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
      expect(formatDuration(172800000)).toEqual([{value: 2, unit: 'days'}]);
      expect(formatDuration(604800000)).toEqual([{value: 1, unit: 'week'}]);
    });

    it('should format weeks correctly', () => {
      expect(formatDuration(604800000)).toEqual([{value: 1, unit: 'week'}]);
      expect(formatDuration(1209600000)).toEqual([{value: 2, unit: 'weeks'}]);
      expect(formatDuration(2419200000)).toEqual([{value: 4, unit: 'weeks'}]);
    });

    it('should format months correctly', () => {
      expect(formatDuration(2592000000)).toEqual([{value: 1, unit: 'month'}]);
      expect(formatDuration(5184000000)).toEqual([{value: 2, unit: 'months'}]);
      expect(formatDuration(7776000000)).toEqual([{value: 3, unit: 'months'}]);
    });

    it('should format years correctly', () => {
      expect(formatDuration(31536000000)).toEqual([{value: 1, unit: 'year'}]);
      expect(formatDuration(63072000000)).toEqual([{value: 2, unit: 'years'}]);
      expect(formatDuration(94608000000)).toEqual([{value: 3, unit: 'years'}]);
    });
  });

  describe('obeys maxValueBeforeNextUnit', () => {
    it('should avoid showing 1000+ of any unit', () => {
      // 1000 seconds should become minutes
      const result = formatDuration(1000000);
      expect(result).toHaveLength(1);
      expect(result[0].unit).toBe('minutes');
      expect(result[0].value).toBeCloseTo(16.666666666666668, 10);

      // 1000 minutes should become hours
      const result2 = formatDuration(60000000);
      expect(result2).toHaveLength(1);
      expect(result2[0].unit).toBe('hours');
      expect(result2[0].value).toBeCloseTo(16.666666666666668, 10);

      // 1000 hours should become days
      const result3 = formatDuration(3600000000);
      expect(result3).toHaveLength(1);
      expect(result3[0].unit).toBe('weeks');
      expect(result3[0].value).toBeCloseTo(5.9523809523809526, 10);
    });
  });

  describe('single significant digit (default)', () => {
    it('should show only the largest unit', () => {
      expect(formatDuration(1500)).toEqual([{value: 1.5, unit: 'seconds'}]);

      const result = formatDuration(65000);
      expect(result).toHaveLength(1);
      expect(result[0].unit).toBe('minutes');
      expect(result[0].value).toBeCloseTo(1.0833333333333333, 10);

      const result2 = formatDuration(3665000);
      expect(result2).toHaveLength(1);
      expect(result2[0].unit).toBe('hours');
      expect(result2[0].value).toBeCloseTo(1.0180555555555556, 10);

      expect(formatDuration(90000000)).toEqual([{value: 25, unit: 'hours'}]);
    });

    it('should round down to the nearest whole unit', () => {
      const result = formatDuration(1999);
      expect(result).toHaveLength(1);
      expect(result[0].unit).toBe('seconds');
      expect(result[0].value).toBeCloseTo(1.999, 10);

      // Test structure and unit separately from the floating-point value
      const result2 = formatDuration(119999);
      expect(result2).toHaveLength(1);
      expect(result2[0].unit).toBe('minutes');
      expect(result2[0].value).toBeCloseTo(1.999983333333333, 10);

      // Test floating-point hours value
      const hoursResult = formatDuration(7199999);
      expect(hoursResult).toHaveLength(1);
      expect(hoursResult[0].unit).toBe('hours');
      expect(hoursResult[0].value).toBeCloseTo(1.9999997222222223, 10);
    });
  });

  describe('two significant digits', () => {
    it('should show two units when remainder exists', () => {
      expect(formatDuration(1500, {significantUnits: 2})).toEqual([
        {value: 1, unit: 'second'},
        {value: 500, unit: 'milliseconds'},
      ]);
      expect(formatDuration(65000, {significantUnits: 2})).toEqual([
        {value: 1, unit: 'minute'},
        {value: 5, unit: 'seconds'},
      ]);
      expect(formatDuration(3665000, {significantUnits: 2})).toEqual([
        {value: 1, unit: 'hour'},
        {value: 1, unit: 'minute'},
      ]);
      expect(formatDuration(90000000, {significantUnits: 2})).toEqual([{unit: 'hours', value: 25}]);
    });

    it('should show only one unit when no remainder', () => {
      expect(formatDuration(1000, {significantUnits: 2})).toEqual([{value: 1, unit: 'second'}]);
      expect(formatDuration(60000, {significantUnits: 2})).toEqual([{value: 1, unit: 'minute'}]);
      expect(formatDuration(3600000, {significantUnits: 2})).toEqual([{value: 1, unit: 'hour'}]);
    });

    it('should handle complex durations', () => {
      expect(formatDuration(3723000, {significantUnits: 2})).toEqual([
        {value: 1, unit: 'hour'},
        {value: 2, unit: 'minutes'},
      ]);
      expect(formatDuration(93784000, {significantUnits: 2})).toEqual([
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

    it('should work with two significant digits', () => {
      expect(formatDuration(1000, {unit: 'seconds', significantUnits: 2})).toEqual([
        {value: 16, unit: 'minutes'},
        {value: 40, unit: 'seconds'},
      ]);
      expect(formatDuration(3665, {unit: 'seconds', significantUnits: 2})).toEqual([
        {value: 1, unit: 'hour'},
        {value: 1, unit: 'minute'},
      ]);
      expect(formatDuration(90000, {unit: 'seconds', significantUnits: 2})).toEqual([
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
      // Test floating-point years value
      const largeResult = formatDuration(Number.MAX_SAFE_INTEGER);
      expect(largeResult).toHaveLength(1);
      expect(largeResult[0].unit).toBe('years');
      expect(largeResult[0].value).toBeCloseTo(285616.41472415626, 10);
    });

    it('should handle fractional milliseconds by flooring', () => {
      // Test floating-point seconds value
      const fractionalResult = formatDuration(1500.7);
      expect(fractionalResult).toHaveLength(1);
      expect(fractionalResult[0].unit).toBe('seconds');
      expect(fractionalResult[0].value).toBeCloseTo(1.5007000000000001, 10);

      expect(formatDuration(1500.7, {significantUnits: 2})).toEqual([
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

      // Video duration - test floating-point minutes value
      const videoResult = formatDuration(215000);
      expect(videoResult).toHaveLength(1);
      expect(videoResult[0].unit).toBe('minutes');
      expect(videoResult[0].value).toBeCloseTo(3.5833333333333335, 10);

      expect(formatDuration(215000, {significantUnits: 2})).toEqual([
        {value: 3, unit: 'minutes'},
        {value: 35, unit: 'seconds'},
      ]);

      // Upload time
      expect(formatDuration(45000)).toEqual([{value: 45, unit: 'seconds'}]);

      // Cache TTL
      expect(formatDuration(3600, {unit: 'seconds'})).toEqual([{value: 1, unit: 'hour'}]);

      // Session timeout
      expect(formatDuration(1800, {unit: 'seconds'})).toEqual([{value: 30, unit: 'minutes'}]);

      // Long-running job - test floating-point hours value
      const jobResult = formatDuration(7532000);
      expect(jobResult).toHaveLength(1);
      expect(jobResult[0].unit).toBe('hours');
      expect(jobResult[0].value).toBeCloseTo(2.0922222222222224, 10);

      expect(formatDuration(7532000, {significantUnits: 2})).toEqual([
        {value: 2, unit: 'hours'},
        {value: 5, unit: 'minutes'},
      ]);
    });
  });
});
