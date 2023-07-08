import {useRouter} from 'next/compat/router';
import {useState, useEffect} from 'react';

import ALL_VERSIONS from '../.versioned_content/_versions.json';

export const latestVersion = ALL_VERSIONS[ALL_VERSIONS.length - 1];

export let defaultVersion = latestVersion;
if (process.env.NEXT_PUBLIC_VERCEL_ENV !== 'production') {
  // We use NEXT_PUBLIC_VERCEL_ENV to default Vercel previews to master because
  // * NEXT_PUBLIC_VERCEL_ENV is exposed to the browser
  // * Vercel previews have NODE_ENV === "production"
  defaultVersion = 'master';
} else if (process.env.NODE_ENV !== 'production') {
  defaultVersion = 'master';
}

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

  // sort release versions by latest - we assume `ALL_VERSIONS` starts with master, and then
  // the following versions are sorted from oldest to latest.
  const sortedVersions = ALL_VERSIONS.slice(0, 1).concat(ALL_VERSIONS.slice(1).reverse());

  return {
    asPath,
    asPathWithoutAnchor,
    version: detectedVersion,
    versions: sortedVersions,
    defaultVersion,
    latestVersion,
  };
}

export function versionFromPage(page: string | string[]) {
  if (Array.isArray(page)) {
    return normalizeVersionPath('/' + page.join('/'), ALL_VERSIONS);
  }

  return normalizeVersionPath(page, ALL_VERSIONS);
}

export const useVersion = () => {
  const router = useRouter();

  const [asPath, setAsPath] = useState('/');

  useEffect(() => {
    if (router.isReady) {
      setAsPath(router.asPath);
    }
  }, [router]);
  return normalizeVersionPath(asPath, ALL_VERSIONS);
};
