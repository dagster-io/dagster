import {formatMetric} from '../formatMetric';
import {ReportingUnitType} from '../types';

describe('formatMetric', () => {
  describe('String value input', () => {
    it('formats large numbers', () => {
      expect(formatMetric('12345', ReportingUnitType.INTEGER)).toBe('12,345');
      expect(formatMetric('12345678', ReportingUnitType.INTEGER)).toBe('12,345,678');

      // Check compact formatting
      expect(
        formatMetric('12345', ReportingUnitType.INTEGER, {
          integerFormat: 'compact',
        }),
      ).toBe('12K');
      expect(
        formatMetric('12345678', ReportingUnitType.INTEGER, {
          integerFormat: 'compact',
        }),
      ).toBe('12M');
    });

    it('formats midsize numbers', () => {
      expect(formatMetric('123', ReportingUnitType.INTEGER)).toBe('123');
      expect(formatMetric('12', ReportingUnitType.INTEGER)).toBe('12');

      // No change with compact formatting
      expect(
        formatMetric('123', ReportingUnitType.INTEGER, {
          integerFormat: 'compact',
        }),
      ).toBe('123');
      expect(
        formatMetric('12', ReportingUnitType.INTEGER, {
          integerFormat: 'compact',
        }),
      ).toBe('12');
    });

    it('formats small numbers', () => {
      expect(formatMetric('1', ReportingUnitType.INTEGER)).toBe('1');
      expect(formatMetric('0.1', ReportingUnitType.INTEGER)).toBe('0.1');
      expect(formatMetric('0.123', ReportingUnitType.INTEGER)).toBe('0.12');
      expect(formatMetric('0', ReportingUnitType.INTEGER)).toBe('0');

      // Placeholder value for very small number
      expect(formatMetric('0.001234', ReportingUnitType.INTEGER)).toBe('<0.01');
    });

    it('formats with max precision', () => {
      expect(
        formatMetric('1', ReportingUnitType.INTEGER, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('1');
      expect(
        formatMetric('0.1', ReportingUnitType.INTEGER, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0.1');
      expect(
        formatMetric('0.0', ReportingUnitType.INTEGER, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0');

      // Truncate at two decimal places because it's above threshold
      expect(
        formatMetric('0.123', ReportingUnitType.INTEGER, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0.12');

      // Maximum precision since it's below threshold, rounding up on last digit.
      expect(
        formatMetric('0.00123456', ReportingUnitType.INTEGER, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0.001235');
    });
  });

  describe('Number value input', () => {
    it('formats large numbers', () => {
      expect(formatMetric(12345, ReportingUnitType.INTEGER)).toBe('12,345');
      expect(formatMetric(12345678, ReportingUnitType.INTEGER)).toBe('12,345,678');

      // Check compact formatting
      expect(
        formatMetric(12345, ReportingUnitType.INTEGER, {
          integerFormat: 'compact',
        }),
      ).toBe('12K');
      expect(
        formatMetric(12345678, ReportingUnitType.INTEGER, {
          integerFormat: 'compact',
        }),
      ).toBe('12M');
    });

    it('formats large floats that are of unit type `INTEGER`', () => {
      // Default formatting: render the decimal.
      expect(formatMetric(12345.123, ReportingUnitType.INTEGER)).toBe('12,345.12');
      expect(formatMetric(12345678.901, ReportingUnitType.INTEGER)).toBe('12,345,678.9');

      // Check compact formatting
      expect(
        formatMetric(12345.123, ReportingUnitType.INTEGER, {
          floatFormat: 'compact-above-threshold',
        }),
      ).toBe('12K');
      expect(
        formatMetric(12345678.901, ReportingUnitType.INTEGER, {
          floatFormat: 'compact-above-threshold',
        }),
      ).toBe('12M');
    });

    it('formats midsize numbers', () => {
      expect(formatMetric(123, ReportingUnitType.INTEGER)).toBe('123');
      expect(formatMetric(12, ReportingUnitType.INTEGER)).toBe('12');

      // No change with compact formatting
      expect(
        formatMetric(123, ReportingUnitType.INTEGER, {
          integerFormat: 'compact',
        }),
      ).toBe('123');
      expect(
        formatMetric(12, ReportingUnitType.INTEGER, {
          integerFormat: 'compact',
        }),
      ).toBe('12');
    });

    it('formats small numbers', () => {
      expect(formatMetric(1, ReportingUnitType.INTEGER)).toBe('1');
      expect(formatMetric(0.1, ReportingUnitType.INTEGER)).toBe('0.1');
      expect(formatMetric(0.123, ReportingUnitType.INTEGER)).toBe('0.12');
      expect(formatMetric(0, ReportingUnitType.INTEGER)).toBe('0');

      // Placeholder value for very small number
      expect(formatMetric(0.001234, ReportingUnitType.INTEGER)).toBe('<0.01');
    });

    it('formats with max precision', () => {
      expect(
        formatMetric(1, ReportingUnitType.INTEGER, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('1');
      expect(
        formatMetric(0.1, ReportingUnitType.INTEGER, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0.1');

      // Truncate at two decimal places because it's above threshold
      expect(
        formatMetric(0.123, ReportingUnitType.INTEGER, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0.12');

      // Maximum precision since it's below threshold, rounding up on last digit.
      expect(
        formatMetric(0.00123456, ReportingUnitType.INTEGER, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0.001235');
    });
  });

  describe('FLOAT unit type', () => {
    it('formats large numbers', () => {
      expect(formatMetric(12345, ReportingUnitType.FLOAT)).toBe('12,345');
      expect(formatMetric(12345678, ReportingUnitType.FLOAT)).toBe('12,345,678');

      // No compact formatting for FLOAT values
      expect(
        formatMetric(12345, ReportingUnitType.FLOAT, {
          integerFormat: 'compact',
        }),
      ).toBe('12,345');
      expect(
        formatMetric(12345678, ReportingUnitType.FLOAT, {
          integerFormat: 'compact',
        }),
      ).toBe('12,345,678');
    });

    it('formats large floats that include decimals', () => {
      // Default formatting: render the decimal.
      expect(formatMetric(12345.123, ReportingUnitType.FLOAT)).toBe('12,345.12');
      expect(formatMetric(12345678.901, ReportingUnitType.FLOAT)).toBe('12,345,678.9');

      // Check compact formatting
      expect(
        formatMetric(12345.123, ReportingUnitType.FLOAT, {
          floatFormat: 'compact-above-threshold',
        }),
      ).toBe('12K');
      expect(
        formatMetric(12345678.901, ReportingUnitType.FLOAT, {
          floatFormat: 'compact-above-threshold',
        }),
      ).toBe('12M');
    });

    it('formats midsize numbers', () => {
      expect(formatMetric(123, ReportingUnitType.FLOAT)).toBe('123');
      expect(formatMetric(12, ReportingUnitType.FLOAT)).toBe('12');
    });

    it('formats small numbers', () => {
      expect(formatMetric(1, ReportingUnitType.FLOAT)).toBe('1');
      expect(formatMetric(0.1, ReportingUnitType.FLOAT)).toBe('0.1');
      expect(formatMetric(0.123, ReportingUnitType.FLOAT)).toBe('0.12');
      expect(formatMetric(0, ReportingUnitType.FLOAT)).toBe('0');

      // Placeholder value for very small number
      expect(formatMetric(0.001234, ReportingUnitType.FLOAT)).toBe('<0.01');
    });

    it('formats with max precision', () => {
      expect(
        formatMetric(1, ReportingUnitType.FLOAT, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('1');
      expect(
        formatMetric(0.1, ReportingUnitType.FLOAT, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0.1');

      // Truncate at two decimal places because it's above threshold
      expect(
        formatMetric(0.123, ReportingUnitType.FLOAT, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0.12');

      // Maximum precision since it's below threshold, rounding up on last digit.
      expect(
        formatMetric(0.00123456, ReportingUnitType.FLOAT, {
          floatPrecision: 'maximum-precision',
        }),
      ).toBe('0.001235');
    });
  });

  describe('Elapsed time formatting', () => {
    it('formats < 1 minute', () => {
      expect(formatMetric(0, ReportingUnitType.TIME_MS)).toBe('0:00:00');
      expect(formatMetric(10, ReportingUnitType.TIME_MS)).toBe('0:00:01');
      expect(formatMetric(5000, ReportingUnitType.TIME_MS)).toBe('0:00:05');
    });

    it('formats < 1 hour', () => {
      expect(formatMetric(10 * 1000, ReportingUnitType.TIME_MS)).toBe('0:00:10');
      expect(formatMetric(60 * 1000, ReportingUnitType.TIME_MS)).toBe('0:01:00');
      expect(formatMetric(59 * 60 * 1000, ReportingUnitType.TIME_MS)).toBe('0:59:00');
    });

    it('formats > 1 hour', () => {
      expect(formatMetric(2 * 60 * 60 * 1000, ReportingUnitType.TIME_MS)).toBe('2:00:00');
      expect(formatMetric(50 * 60 * 60 * 1000, ReportingUnitType.TIME_MS)).toBe('50:00:00');
    });
  });
});
