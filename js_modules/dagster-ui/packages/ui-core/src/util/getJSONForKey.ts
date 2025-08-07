export function getJSONForKey(key: string) {
  let stored = undefined;
  try {
    if (typeof window !== 'undefined') {
      stored = window.localStorage.getItem(key);
    } else {
      stored = self.localStorage.getItem(key);
    }
    if (stored) {
      return JSON.parse(stored);
    }
  } catch {
    if (typeof stored === 'string') {
      // With useStateWithStorage, some values like timezone are moving from `UTC` to `"UTC"`
      // in LocalStorage. To read the old values, pass through raw string values. We can
      // remove this a few months after 0.14.1 is released.
      return stored;
    }
    return undefined;
  }
}
