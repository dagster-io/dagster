import {formatElapsedTime, formatElapsedTimeWithMsec} from './Util';

describe('Elapsed time formatters', () => {
  describe('formatElapsedTime', () => {
    it('formats times under 10s', () => {
      expect(formatElapsedTime(500)).toBe('0.500s');
      expect(formatElapsedTime(5000)).toBe('5.000s');
      expect(formatElapsedTime(-5250)).toBe('-5.250s');
    });

    it('formats times over 10s', () => {
      expect(formatElapsedTime(50000)).toBe('0:00:50');
      expect(formatElapsedTime(500000)).toBe('0:08:20');
      expect(formatElapsedTime(-500000)).toBe('-0:08:20');
      expect(formatElapsedTime(363599999)).toBe('100:59:59');
    });
  });

  describe('formatElapsedTimeWithMsec', () => {
    it('formats times', () => {
      expect(formatElapsedTimeWithMsec(50)).toBe('0:00:00.050');
      expect(formatElapsedTimeWithMsec(50000)).toBe('0:00:50.000');
      expect(formatElapsedTimeWithMsec(500000)).toBe('0:08:20.000');
      expect(formatElapsedTimeWithMsec(-500000)).toBe('-0:08:20.000');
      expect(formatElapsedTimeWithMsec(363599999)).toBe('100:59:59.999');
      expect(formatElapsedTimeWithMsec(-363599999)).toBe('-100:59:59.999');
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

    it('handles decimal correctly in `formatElapsedTime`', () => {
      expect(formatElapsedTime(5000)).toBe('5,000s');
      expect(formatElapsedTime(-5250)).toBe('-5,250s');
    });

    it('handles decimal correctly in `formatElapsedTimeWithMsec`', () => {
      expect(formatElapsedTimeWithMsec(500000)).toBe('0:08:20,000');
      expect(formatElapsedTimeWithMsec(-500000)).toBe('-0:08:20,000');
      expect(formatElapsedTimeWithMsec(363599999)).toBe('100:59:59,999');
    });
  });
});
