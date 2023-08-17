import {timestampToString} from '../time/timestampToString';

const DEC_1_2020 = 1606824000; // Dec 1, 2020 00:00 UTC
const JAN_1_2021 = 1609459200; // Jan 1, 2021 00:00 UTC
const FEB_1_2021 = 1612180800; // Feb 1, 2021 12:00 UTC
const MAR_1_2021 = 1614600000; // Mar 1, 2021 00:00 UTC
const MAR_14_2021 = 1615708800; // Just after DST in USA: Mar 14, 2021 08:00 UTC

describe('timestampToString', () => {
  let dateNow: any = null;
  beforeEach(() => {
    jest.useFakeTimers();
    dateNow = global.Date.now;
    const dateNowStub = jest.fn(() => FEB_1_2021 * 1000);
    global.Date.now = dateNowStub;
  });

  afterEach(() => {
    jest.useRealTimers();
    global.Date.now = dateNow;
  });

  it('formats current year', () => {
    expect(
      timestampToString({
        timestamp: {unix: MAR_1_2021},
        locale: 'en-US',
        timezone: 'America/Chicago',
      }),
    ).toBe('Mar 1, 6:00 AM');
    expect(
      timestampToString({
        timestamp: {unix: MAR_1_2021},
        locale: 'en-US',
        timezone: 'America/Chicago',
        timeFormat: {showSeconds: true, showTimezone: true},
      }),
    ).toBe('Mar 1, 6:00:00 AM CST');
  });

  it('formats previous year', () => {
    expect(
      timestampToString({
        timestamp: {unix: DEC_1_2020},
        locale: 'en-US',
        timezone: 'America/Chicago',
      }),
    ).toBe('Dec 1, 2020, 6:00 AM');
    expect(
      timestampToString({
        timestamp: {unix: DEC_1_2020},
        locale: 'en-US',
        timezone: 'America/Chicago',
        timeFormat: {showSeconds: true, showTimezone: true},
      }),
    ).toBe('Dec 1, 2020, 6:00:00 AM CST');
  });

  it('identifies year across New Year', () => {
    expect(
      timestampToString({
        timestamp: {unix: JAN_1_2021},
        locale: 'en-US',
        timezone: 'America/Chicago',
      }),
    ).toBe('Dec 31, 2020, 6:00 PM');
    expect(
      timestampToString({
        timestamp: {unix: JAN_1_2021},
        locale: 'en-US',
        timezone: 'Europe/Berlin',
        timeFormat: {showSeconds: true, showTimezone: true},
      }),
    ).toBe('Jan 1, 1:00:00 AM GMT+1');
  });

  it('identifies DST across boundaries', () => {
    expect(
      timestampToString({
        timestamp: {unix: MAR_14_2021},
        locale: 'en-US',
        timezone: 'America/Chicago',
      }),
    ).toBe('Mar 14, 3:00 AM');
    expect(
      timestampToString({
        timestamp: {unix: MAR_14_2021},
        locale: 'en-US',
        timezone: 'Europe/Berlin',
        timeFormat: {showSeconds: true, showTimezone: true},
      }),
    ).toBe('Mar 14, 9:00:00 AM GMT+1');
  });
});
