import {calculateMiddleTruncation} from './calculateMiddleTruncation';

describe('calculateMiddleTruncation', () => {
  it('skips the loop if the given text will fit', () => {
    const measure = jest.fn(() => 80);
    expect(calculateMiddleTruncation('hello', 100, measure)).toBe('hello');
    expect(measure.mock.calls).toHaveLength(1);
  });

  it('uses a binary search to find the right truncation point', () => {
    const text = 'hello world';

    // Let's say it's 10 pixels per character. We want to fit within 80 pixels.
    const targetWidth = 80;
    const measure = jest.fn((value: string) => value.length * 10);

    const result = calculateMiddleTruncation(text, targetWidth, measure);
    const calls = measure.mock.calls;

    // First, check the text as-is.
    expect(calls[0]).toEqual(['hello world']);

    // The text is 11 characters long. Half of that, floored, is 5. "start" = 1, "end" = 5, "midpoint" = 3.
    expect(calls[1]).toEqual(['hel…rld']);

    // That result provided a width of 70, which fits. Continue the search, in the direction of 5.
    // "start" = 4, "end" = 5, "midpoint" = 4
    expect(calls[2]).toEqual(['hell…orld']);

    // That result provided a width of 90, which does not fit. "start" = 4, "end" = 3. The loop ends.
    expect(calls).toHaveLength(3);
    expect(result).toBe('hel…rld');
  });

  it('is also successful with a longer string', () => {
    // String of length 74
    const text = 'four score and seven years ago our fathers brought forth on this continent';

    // Let's say it's 10 pixels per character. We want to fit within 200 pixels.
    const targetWidth = 200;
    const measure = jest.fn((value: string) => value.length * 10);

    const result = calculateMiddleTruncation(text, targetWidth, measure);
    const calls = measure.mock.calls;

    // First, check the text as-is.
    expect(calls[0]).toEqual([text]);

    // The text is 74 characters long. Half of that, floored, is 37. Binary search between 1 and 37.
    // The first "midpoint" is 19.
    expect(calls[1]).toEqual(['four score and seve…h on this continent']);

    // That result provided a width of 390, which does not fit. Continue the search, in the direction of 1.
    // "start" = 1, "end" = 18, "midpoint" = 9.
    expect(calls[2]).toEqual(['four scor…continent']);

    // That result provided a width of 190, which fits. "start" = 10, "end" = 18, "midpoint" = 14.
    expect(calls[3]).toEqual(['four score and…this continent']);

    // That result provided a width of 290, which does not fit. "start" = 10, "end" = 13, "midpoint" = 11.
    expect(calls[4]).toEqual(['four score …s continent']);

    // That result provided a width of 220, which does not fit. "start" = 10, "end" = 10, "midpoint" = 10.
    expect(calls[5]).toEqual(['four score… continent']);

    // That result provided a width of 210, which does not fit. "start" = 10, "end" = 9. The loop ends.
    // The text is sliced at the `end` value, which is 9.
    expect(calls).toHaveLength(6);
    expect(result).toBe('four scor…continent');
    expect(measure(result)).toBe(190);
  });

  it('is successful with even number divisions', () => {
    // String of length 32
    const text = 'abcdefghijklmnopqrstuvwxyz012345';

    // Let's say it's 10 pixels per character. We want to fit within 200 pixels.
    const targetWidth = 100;
    const measure = jest.fn((value: string) => value.length * 10);

    const result = calculateMiddleTruncation(text, targetWidth, measure);
    const calls = measure.mock.calls;

    // First, check the text as-is.
    expect(calls[0]).toEqual([text]);

    // The text is 32 characters long. Half of that 16. Binary search between 1 and 16.
    // The first "midpoint" is 8.
    expect(calls[1]).toEqual(['abcdefgh…yz012345']);

    // That result provided a width of 170, which does not fit. Continue the search, in the direction of 1.
    // "start" = 1, "end" = 7, "midpoint" = 4.
    expect(calls[2]).toEqual(['abcd…2345']);

    // That result provided a width of 90, which fits. "start" = 5, "end" = 7, "midpoint" = 6.
    expect(calls[3]).toEqual(['abcdef…012345']);

    // That result provided a width of 130, which does not fit. "start" = 5, "end" = 5, "midpoint" = 5.
    expect(calls[4]).toEqual(['abcde…12345']);

    // That result provided a width of 110, which does not fit. "start" = 5, "end" = 4. The loop ends.
    // The text is sliced at the `end` value, which is 4.
    expect(calls).toHaveLength(5);
    expect(result).toBe('abcd…2345');
    expect(measure(result)).toBe(90);
  });
});
