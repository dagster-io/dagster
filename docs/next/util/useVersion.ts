import ALL_VERSIONS from '../.versioned_content/_versions.json';
import MAP_VERSION_TO_LINK from '../.versioned_content/_versions_with_static_links.json';

export const latestVersion = ALL_VERSIONS[ALL_VERSIONS.length - 1];

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
let showVersionNotice = true;
if (process.env.NEXT_PUBLIC_VERCEL_ENV === 'production') {
  // We use NEXT_PUBLIC_VERCEL_ENV to tell whether it's in production or not, because:
  // * NEXT_PUBLIC_VERCEL_ENV is exposed to the browser
  // * Vercel previews have NODE_ENV === "production", so we can't rely on that.
  //     As going forward, we are relying on Vercel's previews to version the older docs, we need to
  //     make sure that when a user lands on the older docs (aka previews), we have the version
  //     notice as reminder that they are looking at older docs.
  showVersionNotice = false;
}

export const useVersion = () => {
  return {version: latestVersion, showVersionNotice};
};
