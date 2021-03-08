const ALL_VERSIONS = ["master"];
const defaultVersion = "master";

import React, { useEffect, useState } from "react";

import { useRouter } from "next/router";

export function normalizeVersionPath(
  asPath: string,
  versions?: string[]
): {
  version?: string;
  asPath: string;
  versions: string[];
  defaultVersion: string;
} {
  let detectedVersion: string = defaultVersion;
  // first item will be empty string from splitting at first char
  const pathnameParts = asPath.split("/");

  (versions || []).some((version) => {
    if (pathnameParts[1].toLowerCase() === version.toLowerCase()) {
      detectedVersion = version;
      pathnameParts.splice(1, 1);
      asPath = pathnameParts.join("/") || "/";
      return true;
    }
    return false;
  });

  return {
    asPath,
    version: detectedVersion,
    versions: ALL_VERSIONS,
    defaultVersion,
  };
}

export function versionFromPage(page: string | string[]) {
  if (Array.isArray(page)) {
    return normalizeVersionPath("/" + page.join("/"), ALL_VERSIONS);
  }

  return normalizeVersionPath(page, ALL_VERSIONS);
}

export const useVersion = () => {
  const router = useRouter();
  const [asPath, setAsPath] = useState("/");

  useEffect(() => {
    if (router.isReady) {
      setAsPath(router.asPath);
    }
  }, [router]);

  return normalizeVersionPath(asPath, ALL_VERSIONS);
};
