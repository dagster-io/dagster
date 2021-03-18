import { useEffect, useState } from "react";

import ALL_VERSIONS from "../.versioned_content/_versions.json";
import { useRouter } from "next/router";

const defaultVersion = "master";

export function normalizeVersionPath(
  asPath: string,
  versions?: string[]
): {
  version?: string;
  asPath: string;
  asPathWithoutAnchor: string;
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

  let asPathWithoutAnchor = asPath;
  if (asPathWithoutAnchor.indexOf("#") > 0) {
    asPathWithoutAnchor = asPath.substring(0, asPath.indexOf("#"));
  }

  return {
    asPath,
    asPathWithoutAnchor,
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
