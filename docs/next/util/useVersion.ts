import {useRouter} from 'next/router';
import {useState, useEffect} from 'react';

import ALL_VERSIONS from '../.versioned_content/_versions.json';

// sort release versions by latest first
const SORTED_ALL_VERSIONS = ALL_VERSIONS.reverse();
export const latestVersion = SORTED_ALL_VERSIONS[0];
export const defaultVersion = latestVersion;
// if (process.env.NEXT_PUBLIC_VERCEL_ENV !== 'production') {
//   // We use NEXT_PUBLIC_VERCEL_ENV to default Vercel previews to master because
//   // * NEXT_PUBLIC_VERCEL_ENV is exposed to the browser
//   // * Vercel previews have NODE_ENV === "production"
//   defaultVersion = 'master';
// } else if (process.env.NODE_ENV !== 'production') {
//   defaultVersion = 'master';
// }

export function normalizeVersionPath(
  asPath: string,
  versions?: string[],
): {
  version?: string;
  asPath: string;
  asPathWithoutAnchor: string;
  versions: string[];
  defaultVersion: string;
  latestVersion: string;
} {
  let detectedVersion: string = defaultVersion;
  // first item will be empty string from splitting at first char
  const pathnameParts = asPath.split('/');

  (versions || []).some((version) => {
    if (pathnameParts[1].toLowerCase() === version.toLowerCase()) {
      detectedVersion = version;
      pathnameParts.splice(1, 1);
      asPath = pathnameParts.join('/') || '/';
      return true;
    }
    return false;
  });

  let asPathWithoutAnchor = asPath;
  if (asPathWithoutAnchor.indexOf('#') > 0) {
    asPathWithoutAnchor = asPath.substring(0, asPath.indexOf('#'));
  }

  return {
    asPath,
    asPathWithoutAnchor,
    version: detectedVersion,
    versions: SORTED_ALL_VERSIONS,
    defaultVersion,
    latestVersion,
  };
}

export function versionFromPage(page: string | string[]) {
  if (Array.isArray(page)) {
    return normalizeVersionPath('/' + page.join('/'), SORTED_ALL_VERSIONS);
  }

  return normalizeVersionPath(page, SORTED_ALL_VERSIONS);
}

export const useVersion = () => {
  const router = useRouter();

  const [asPath, setAsPath] = useState('/');

  useEffect(() => {
    if (router.isReady) {
      setAsPath(router.asPath);
    }
  }, [router]);
  return normalizeVersionPath(asPath, SORTED_ALL_VERSIONS);
};
