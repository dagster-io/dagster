import {humanCronString} from './humanCronString';

describe('humanCronString', () => {
  it('parses special strings correctly', () => {
    expect(humanCronString('@daily')).toBe('At 12:00 AM');
    expect(humanCronString('@weekly')).toBe('At 12:00 AM, only on Sunday');
    expect(humanCronString('@monthly')).toBe('At 12:00 AM, on day 1 of the month');
  });
});
