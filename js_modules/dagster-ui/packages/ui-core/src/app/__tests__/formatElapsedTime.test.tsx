import {formatElapsedTimeWithoutMsec, formatElapsedTimeWithMsec} from '../Util';

const SECOND = 1 * 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;

describe('Elapsed time formatters', () => {
  describe('formatElapsedTimeWithoutMsec', () => {
    it('formats times between -1 and 1 seconds', () => {
      expect(formatElapsedTimeWithoutMsec(0)).toBe('0:00:00');
      expect(formatElapsedTimeWithoutMsec(1)).toBe('0:00:01');
      expect(formatElapsedTimeWithoutMsec(500)).toBe('0:00:01');
      expect(formatElapsedTimeWithoutMsec(-500)).toBe('-0:00:01');
    });

    it('formats times under 10s', () => {
      expect(formatElapsedTimeWithoutMsec(5000)).toBe('0:00:05');
      expect(formatElapsedTimeWithoutMsec(-5250)).toBe('-0:00:05');
    });

    it('formats times over 10s', () => {
      expect(formatElapsedTimeWithoutMsec(50000)).toBe('0:00:50');
      expect(formatElapsedTimeWithoutMsec(500000)).toBe('0:08:20');
      expect(formatElapsedTimeWithoutMsec(-500000)).toBe('-0:08:20');
      expect(formatElapsedTimeWithoutMsec(363599999)).toBe('100:59:59');
    });
  });

  describe('formatElapsedTimeWithMsec', () => {
    it('formats times', () => {
      expect(formatElapsedTimeWithMsec(50)).toBe('0.050');
      expect(formatElapsedTimeWithMsec(50000)).toBe('50.000');
      expect(formatElapsedTimeWithMsec(500000)).toBe('8:20.000');
      expect(formatElapsedTimeWithMsec(-500000)).toBe('-8:20.000');
      expect(formatElapsedTimeWithMsec(363599999)).toBe('100:59:59.999');
      expect(formatElapsedTimeWithMsec(-363599999)).toBe('-100:59:59.999');

      expect(formatElapsedTimeWithMsec(HOUR + MINUTE + SECOND + 69)).toBe('1:01:01.069');
      expect(formatElapsedTimeWithMsec(HOUR + SECOND + 69)).toBe('1:00:01.069');
      expect(formatElapsedTimeWithMsec(HOUR + 69)).toBe('1:00:00.069');
      expect(formatElapsedTimeWithMsec(MINUTE + 69)).toBe('1:00.069');
      expect(formatElapsedTimeWithMsec(SECOND + 69)).toBe('1.069');
      expect(formatElapsedTimeWithMsec(69)).toBe('0.069');
    });
  });

  describe('Internationalization for decimal point', () => {
    let languageGetter;

    beforeAll(() => {
      languageGetter = jest.spyOn(global.navigator, 'language', 'get');
      languageGetter.mockReturnValue('es-ES');
    });

    afterAll(() => {
      jest.clearAllMocks();
    });

    it('is unchanged in `formatElapsedTimeWithoutMsec`', () => {
      expect(formatElapsedTimeWithoutMsec(0)).toBe('0:00:00');
      expect(formatElapsedTimeWithoutMsec(1)).toBe('0:00:01');
      expect(formatElapsedTimeWithoutMsec(500)).toBe('0:00:01');
      expect(formatElapsedTimeWithoutMsec(-500)).toBe('-0:00:01');
    });

    it('handles decimal correctly in `formatElapsedTimeWithMsec`', () => {
      expect(formatElapsedTimeWithMsec(500000)).toBe('8:20,000');
      expect(formatElapsedTimeWithMsec(-500000)).toBe('-8:20,000');
      expect(formatElapsedTimeWithMsec(363599999)).toBe('100:59:59,999');
    });
  });
});
