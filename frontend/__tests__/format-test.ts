// Pure helpers used on the request screens. Dates are synthetic.
import { addDays, formatPeriod, formatTime, isoDate } from '@/lib/format';

describe('formatPeriod', () => {
  test('shows the two dates and the number of days of a Postgres range', () => {
    expect(formatPeriod('["2026-10-23 05:00:00+05","2026-10-26 05:00:00+05")')).toBe('Oct 23 – Oct 26 · 3 days');
  });

  test('uses the singular for one day', () => {
    expect(formatPeriod('["2026-10-23 00:00:00+00","2026-10-24 00:00:00+00")')).toBe('Oct 23 – Oct 24 · 1 day');
  });

  test('returns text it cannot parse unchanged', () => {
    expect(formatPeriod('not a range')).toBe('not a range');
  });
});

describe('date helpers', () => {
  test('addDays works in UTC and does not change its input', () => {
    const d = new Date('2026-10-31T00:00:00Z');
    expect(isoDate(addDays(d, 1))).toBe('2026-11-01');
    expect(isoDate(d)).toBe('2026-10-31');
  });

  test('formatTime shows the UTC clock time', () => {
    expect(formatTime('2026-10-01T08:05:00Z')).toBe('Oct 1, 08:05 UTC');
  });
});
