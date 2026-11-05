import {useEffect} from 'react';

// Unattended screens pick up new deploys by themselves. On load the page fetches its own HTML
// and notes the script bundles it names; every few minutes it fetches again and compares.
// Each build ships new hashed bundle names, so a difference means a new version is live,
// and the page reloads itself to run it.
const CHECK_EVERY_MS = 5 * 60 * 1000;
const RELOADED_FOR_KEY = 'hp-build-reload-for';

const bundleNames = (html: string) => {
  const names: string[] = [];
  const pattern = /<script[^>]+src="([^"]+)"/g;
  let match = pattern.exec(html);
  while (match) {
    names.push(match[1] ?? '');
    match = pattern.exec(html);
  }
  return names.sort().join('\n');
};

const fetchBundleNames = async (): Promise<string | null> => {
  try {
    const res = await fetch(window.location.pathname, {
      cache: 'no-store',
      headers: {Accept: 'text/html'},
    });
    if (!res.ok) {
      return null;
    }
    return bundleNames(await res.text()) || null;
  } catch {
    // Offline or mid-deploy: try again next time.
    return null;
  }
};

export const useReloadOnNewBuild = () => {
  useEffect(() => {
    let baseline: string | null = null;

    const check = async () => {
      const served = await fetchBundleNames();
      if (!served) {
        return;
      }
      if (!baseline) {
        baseline = served;
        return;
      }
      if (served === baseline || window.sessionStorage.getItem(RELOADED_FOR_KEY) === served) {
        return;
      }
      window.sessionStorage.setItem(RELOADED_FOR_KEY, served);
      window.location.reload();
    };

    check();
    const timer = setInterval(check, CHECK_EVERY_MS);
    return () => clearInterval(timer);
  }, []);
};

// "Refresh every screen" button in Settings. The webserver keeps the time of the last
// request; each open page polls it and reloads when it moves. The value last seen is kept
// in sessionStorage so a page does not reload again for a request it already acted on,
// and the page that pressed the button records the new value itself so it stays put.
const REFRESH_URL = '/hillpointe/refresh';
const REFRESH_EVERY_MS = 30 * 1000;
const REFRESH_SEEN_KEY = 'hp-refresh-seen';

const refreshStamp = async (method: 'GET' | 'POST'): Promise<string | null> => {
  try {
    const res = await fetch(REFRESH_URL, {method, cache: 'no-store'});
    if (!res.ok) {
      return null;
    }
    const body = await res.json();
    return typeof body.at === 'number' ? String(body.at) : null;
  } catch {
    return null;
  }
};

/** Ask every open screen to reload. Resolves false if the server did not take it. */
export const requestRefreshEverywhere = async (): Promise<boolean> => {
  const stamp = await refreshStamp('POST');
  if (!stamp) {
    return false;
  }
  window.sessionStorage.setItem(REFRESH_SEEN_KEY, stamp);
  return true;
};

export const useReloadOnRemoteRefresh = () => {
  useEffect(() => {
    const check = async () => {
      const stamp = await refreshStamp('GET');
      if (!stamp) {
        return;
      }
      const seen = window.sessionStorage.getItem(REFRESH_SEEN_KEY);
      window.sessionStorage.setItem(REFRESH_SEEN_KEY, stamp);
      if (seen && seen !== stamp) {
        window.location.reload();
      }
    };
    check();
    const timer = setInterval(check, REFRESH_EVERY_MS);
    return () => clearInterval(timer);
  }, []);
};
