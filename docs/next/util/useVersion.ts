import {useRouter} from 'next/router';
import {useState, useEffect} from 'react';

import ALL_VERSIONS from '../.versioned_content/_versions.json';
import MAP_VERSION_TO_LINK from '../.versioned_content/_versions_with_static_links.json';

export const latestVersion = ALL_VERSIONS[ALL_VERSIONS.length - 1];
export const defaultVersion = latestVersion; // always point the default version to master

export function getOlderVersions() {
  // exclude latest version which will be the current site. sort by version desc
  return MAP_VERSION_TO_LINK.slice(0, -1).sort((a, b) => (a.version < b.version ? 1 : -1));
<<<<<<< HEAD
}

// only hide version notice in production
export let showVersionNotice = true;
if (process.env.NEXT_PUBLIC_VERCEL_ENV === 'production') {
  // We use NEXT_PUBLIC_VERCEL_ENV to tell whether it's in production or not
  // * NEXT_PUBLIC_VERCEL_ENV is exposed to the browser
  // * Vercel previews have NODE_ENV === "production"
  showVersionNotice = false;
} else if (process.env.NODE_ENV === 'production') {
  // for testing
  showVersionNotice = false;
=======
>>>>>>> 6dc1a92f2b ([docs-no-version] 1/ version dropdown points to static link)
}

// only hide version notice in production
export let showVersionNotice = true;
if (process.env.NEXT_PUBLIC_VERCEL_ENV === 'production') {
  // We use NEXT_PUBLIC_VERCEL_ENV to tell whether it's in production or not
  // * NEXT_PUBLIC_VERCEL_ENV is exposed to the browser
  // * Vercel previews have NODE_ENV === "production"
  showVersionNotice = false;
} else if (process.env.NODE_ENV === 'production') {
  // for testing
  showVersionNotice = false;
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
