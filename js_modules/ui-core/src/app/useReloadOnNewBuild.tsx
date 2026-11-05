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
