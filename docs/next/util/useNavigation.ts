import masterNavigation from "../../content/_navigation.json";
import { useVersion, latestVersion, defaultVersion } from "./useVersion";
import versionedNavigation from "../.versioned_content/_versioned_navigation.json";

type NavEntry = {
  title: string;
  path: string;
  children?: NavEntry[];
  icon?: string;
  isUnversioned?: boolean;
  isExternalLink?: boolean;
};

export const getNavKey = (parentKey: string, idx: number) => {
  return parentKey ? `${parentKey}-${idx}` : `${idx}`;
};

export const getNavLvl = (navKey: string) => {
  return navKey.split("-").length - 1;
};

export function flatten(yx: any, parentKey: string = "") {
  const xs = JSON.parse(JSON.stringify(yx));

  return xs.reduce((acc: any, x: any, idx: number) => {
    const navKey = getNavKey(parentKey, idx);
    // console.log(navKey, x);
    acc = acc.concat({ key: navKey, ...x });
    if (x.children) {
      acc = acc.concat(flatten(x.children, navKey));
      x.children = [];
    }
    return acc;
  }, []);
}

export const useNavigation = () => {
  const { version } = useVersion();

  if (version === "master") {
    return masterNavigation;
  }

  return versionedNavigation[version];
};

export const latestAllPaths = () => {
  // latest version
  return flatten(versionedNavigation[latestVersion])
    .filter((n: { path: any }) => n.path)
    .map(({ path }) => path.split("/").splice(1))
    .map((page: string[]) => {
      return {
        params: {
          page: page,
        },
      };
    });
};

export const latestAllVersionedPaths = () => {
  const navigationForLatestVersion =
    defaultVersion === "master" // when it's not in prod, the latest version defaults to master
      ? masterNavigation
      : versionedNavigation[defaultVersion];

  return flatten(navigationForLatestVersion)
    .filter((n: NavEntry) => n.path && !n.isExternalLink && !n.isUnversioned)
    .map(({ path }) => path.split("/").splice(1))
    .map((page: string[]) => {
      return {
        params: {
          page: page,
        },
      };
    });
};

export const allPaths = () => {
  let paths = [];

  // Master
  const flattenedMasterNavigation = flatten(masterNavigation)
    .filter((n: { path: any }) => n.path)
    .map(({ path }) => path.split("/").splice(1))
    .map((page: string[]) => {
      return {
        params: {
          page: ["master", ...page],
        },
      };
    });

  paths = [...flattenedMasterNavigation, ...paths];

  // Always enable versioning when on Vercel
  if (process.env.VERCEL || !__VERSIONING_DISABLED__) {
    for (const [key, value] of Object.entries(versionedNavigation)) {
      const flattenedVersionNavigation = flatten(value)
        .filter((n: { path: any }) => n.path)
        .map(({ path }) => [key, ...path.split("/").splice(1)])
        .map((page: string[]) => {
          return {
            params: {
              page: page,
            },
          };
        });

      paths = [...paths, ...flattenedVersionNavigation];
    }
  }

  return paths;
};

export const navigations = {
  masterNavigation,
  versionedNavigation,
};
