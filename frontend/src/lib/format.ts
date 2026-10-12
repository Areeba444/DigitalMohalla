const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** Postgres range text like ["2026-10-23 05:00:00+05","2026-10-26 05:00:00+05") -> two Dates. */
function parseRange(period: string): [Date, Date] | null {
  const stamps = period.match(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}(?::?\d{2})?/g);
  if (!stamps || stamps.length < 2) return null;
  const toDate = (s: string) => {
    const iso = s.replace(' ', 'T').replace(/([+-]\d{2})$/, '$1:00');
    return new Date(iso);
  };
  return [toDate(stamps[0]), toDate(stamps[1])];
}

const day = (d: Date) => `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}`;

/** "Oct 23 – Oct 26 · 3 days". Requests are made in whole UTC days, so UTC fields are shown. */
export function formatPeriod(period: string): string {
  const range = parseRange(period);
  if (!range) return period;
  const [start, end] = range;
  const days = Math.max(1, Math.round((end.getTime() - start.getTime()) / 86_400_000));
  return `${day(start)} – ${day(end)} · ${days} day${days === 1 ? '' : 's'}`;
}

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function addDays(d: Date, n: number): Date {
  const copy = new Date(d.getTime());
  copy.setUTCDate(copy.getUTCDate() + n);
  return copy;
}

export function formatTime(iso: string): string {
  const d = new Date(iso);
  return `${day(d)}, ${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')} UTC`;
}
