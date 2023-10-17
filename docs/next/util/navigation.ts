import navigation from '../../content/_navigation.json';

type NavEntry = {
  title: string;
  path: string;
  children?: NavEntry[];
  icon?: string;
  isNotDynamic?: boolean;
  isExternalLink?: boolean;
};

export const getNavKey = (parentKey: string, idx: number) => {
  return parentKey ? `${parentKey}-${idx}` : `${idx}`;
};

export const getNavLvl = (navKey: string) => {
  return navKey.split('-').length - 1;
};

export function flatten(yx: any, parentKey = '') {
  const xs = JSON.parse(JSON.stringify(yx));

  return xs.reduce((acc: any, x: any, idx: number) => {
    const navKey = getNavKey(parentKey, idx);
    // console.log(navKey, x);
    acc = acc.concat({key: navKey, ...x});
    if (x.children) {
      acc = acc.concat(flatten(x.children, navKey));
      x.children = [];
    }
    return acc;
  }, []);
}

const FULL_URL_REGEX = /https?:\/\//;

export const latestAllPaths = () => {
  // Include paths like /changelog, which don't go through the markdoc renderer.
  // Skip any full URLs, as these don't belong in the sitemap.
  return flatten(navigation)
    .filter((n: {path: any}) => n.path && !FULL_URL_REGEX.test(n.path))
    .map(({path}) => path.split('/').splice(1))
    .map((page: string[]) => {
      return {
        params: {
          page,
        },
      };
    });
};

export const latestAllDynamicPaths = () => {
  // only include paths that will be dynamically generated
  return flatten(navigation)
    .filter((n: NavEntry) => n.path && !n.isExternalLink && !n.isNotDynamic)
    .map(({path}) => path.split('/').splice(1))
    .map((page: string[]) => {
      return {
        params: {
          page,
        },
      };
    });
};

export default navigation;
