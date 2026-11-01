import {createContext, useCallback, useContext, useEffect, useLayoutEffect, useMemo} from 'react';
import {useLocation, useRouteMatch} from 'react-router-dom';
import {atom, useRecoilValue, useSetRecoilState} from 'recoil';

// `pathname` and `depth` identify the `Route` that set `path`, so `useClaimCurrentPage` can
// keep the innermost one.
type CurrentPage = {path: string; specificPath: string; pathname?: string; depth?: number};

export const currentPageAtom = atom<CurrentPage>({
  key: 'currentPageAtom',
  default: {path: '/', specificPath: '/'},
});

// Same rule as the mobile route status: layout effects run child-first, so an enclosing
// route's write for the same pathname is rejected rather than overwriting its leaf.
export const useClaimCurrentPage = () => {
  const setCurrentPage = useSetRecoilState(currentPageAtom);
  return useCallback(
    ({path, pathname, depth}: {path: string; pathname: string; depth: number}) => {
      setCurrentPage((prev) => {
        if (prev.pathname === pathname && prev.depth !== undefined && prev.depth > depth) {
          return prev;
        }
        return {specificPath: prev.specificPath, path, pathname, depth};
      });
    },
    [setCurrentPage],
  );
};

/**
 * Append `suffix` (e.g. `?view=events`) to the enclosing route's page name, for pages whose
 * name depends on state the route can't see.
 * - Re-applies when the pathname changes, since the route rewrites the bare path then even
 *   if this component stays mounted.
 * - Keeps the route's `pathname`/`depth`, so enclosing routes still can't overwrite it.
 */
export const useRefineCurrentPage = (suffix: string) => {
  const setCurrentPage = useSetRecoilState(currentPageAtom);
  const {path} = useRouteMatch();
  const {pathname} = useLocation();
  useEffect(() => {
    setCurrentPage((prev) => ({...prev, path: `${path}${suffix}`}));
  }, [path, pathname, suffix, setCurrentPage]);
};

export interface GenericAnalytics {
  group?: (groupId: string, traits?: Record<string, any>) => void;
  identify?: (userId: string, traits?: Record<string, any>) => void;
  page: (
    path: string,
    specificPath: string,
    properties?: Record<string, string | undefined>,
  ) => void;
  track: (eventName: string, properties?: Record<string, any>) => void;
}

// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
export const AnalyticsContext = createContext<GenericAnalytics>(undefined!);

const PAGEVIEW_DELAY = 300;

export const usePageContext = () => {
  return useRecoilValue(currentPageAtom);
};

const useAnalytics = () => {
  const analytics = useContext(AnalyticsContext);
  if (!analytics && typeof 'jest' === undefined && !process.env.STORYBOOK) {
    throw new Error('Analytics may only be used within `AnalyticsContext.Provider`.');
  }
  return analytics;
};

export const dummyAnalytics = () => ({
  group: (groupId: string, traits?: Record<string, any>) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Group]', groupId, traits);
    }
  },
  identify: (id: string, traits?: Record<string, any>) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Identify]', id, traits);
    }
  },
  page: (
    path: string,
    specificPath: string,
    properties: Record<string, string | undefined> = {},
  ) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Pageview]', {path, specificPath, ...properties});
    }
  },
  track: (eventName: string, properties?: Record<string, any>) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Event]', eventName, properties);
    }
  },
});

export const useTrackPageView = (memoizedProperties?: Record<string, string | undefined>) => {
  const analytics = useAnalytics();
  const match = useRouteMatch();
  const {pathname: specificPath} = useLocation();
  const {path} = match;

  useLayoutEffect(() => {
    const timer = setTimeout(() => {
      analytics.page(path, specificPath, memoizedProperties);
    }, PAGEVIEW_DELAY);

    return () => {
      clearTimeout(timer);
    };
  }, [analytics, path, specificPath, memoizedProperties]);
};

export const useTrackAssetPageView = (assetView: string | undefined) => {
  const properties = useMemo(() => (assetView ? {assetView} : undefined), [assetView]);
  useTrackPageView(properties);
};

export const useTrackEvent = () => {
  const analytics = useAnalytics();
  const match = useRouteMatch();
  const {pathname: specificPath} = useLocation();
  const {path} = match;

  return useCallback(
    (eventName: string, properties?: Record<string, any>) => {
      analytics.track(eventName, {...properties, path, specificPath});
    },
    [analytics, path, specificPath],
  );
};
