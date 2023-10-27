import MAP_VERSION_TO_LINK from '../.versioned_content/_versions_with_static_links.json';

export const LATEST_VERSION = MAP_VERSION_TO_LINK[MAP_VERSION_TO_LINK.length - 1].version;

export function getOlderVersions() {
  // exclude latest version which will be the current site. sort by version desc
  return MAP_VERSION_TO_LINK.slice(0, -1).sort((a, b) => (a.version < b.version ? 1 : -1));
}

// only hide version notice in production
export let SHOW_VERSION_NOTICE = true;
if (process.env.NEXT_PUBLIC_VERCEL_ENV === 'production') {
  // We use NEXT_PUBLIC_VERCEL_ENV to tell whether it's in production or not, because:
  // * NEXT_PUBLIC_VERCEL_ENV is exposed to the browser
  // * Vercel previews have NODE_ENV === "production", so we can't rely on that.
  //     As going forward, we are relying on Vercel's previews to version the older docs, we need to
  //     make sure that when a user lands on the older docs (aka previews), we have the version
  //     notice as reminder that they are looking at older docs.
  SHOW_VERSION_NOTICE = false;
}
