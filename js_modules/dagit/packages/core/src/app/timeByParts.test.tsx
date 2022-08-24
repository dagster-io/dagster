import {timeByParts} from './timeByParts';

describe('timeByParts', () => {
  it('parses millisecond-only values', () => {
    expect(timeByParts(120)).toEqual({
      hours: 0,
      minutes: 0,
      seconds: 0,
      milliseconds: 120,
    });

    expect(timeByParts(-120)).toEqual({
      hours: 0,
      minutes: 0,
      seconds: 0,
      milliseconds: 120,
    });
  });

  it('parses seconds and milliseconds', () => {
    expect(timeByParts(8000)).toEqual({
      hours: 0,
      minutes: 0,
      seconds: 8,
      milliseconds: 0,
    });

    expect(timeByParts(8250)).toEqual({
      hours: 0,
      minutes: 0,
      seconds: 8,
      milliseconds: 250,
    });

    expect(timeByParts(-18250)).toEqual({
      hours: 0,
      minutes: 0,
      seconds: 18,
      milliseconds: 250,
    });
  });

  it('parses minutes, seconds, and milliseconds', () => {
    expect(timeByParts(60000)).toEqual({
      hours: 0,
      minutes: 1,
      seconds: 0,
      milliseconds: 0,
    });

    expect(timeByParts(63250)).toEqual({
      hours: 0,
      minutes: 1,
      seconds: 3,
      milliseconds: 250,
    });

    expect(timeByParts(-63250)).toEqual({
      hours: 0,
      minutes: 1,
      seconds: 3,
      milliseconds: 250,
    });

    expect(timeByParts(123250)).toEqual({
      hours: 0,
      minutes: 2,
      seconds: 3,
      milliseconds: 250,
    });

    expect(timeByParts(3599999)).toEqual({
      hours: 0,
      minutes: 59,
      seconds: 59,
      milliseconds: 999,
    });
  });

  it('parses hours, minutes, seconds, and milliseconds', () => {
    expect(timeByParts(3600000)).toEqual({
      hours: 1,
      minutes: 0,
      seconds: 0,
      milliseconds: 0,
    });

    expect(timeByParts(-3600000)).toEqual({
      hours: 1,
      minutes: 0,
      seconds: 0,
      milliseconds: 0,
    });

    expect(timeByParts(360000000)).toEqual({
      hours: 100,
      minutes: 0,
      seconds: 0,
      milliseconds: 0,
    });

    expect(timeByParts(363599999)).toEqual({
      hours: 100,
      minutes: 59,
      seconds: 59,
      milliseconds: 999,
    });
  });
});
