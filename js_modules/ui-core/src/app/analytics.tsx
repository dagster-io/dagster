import {createContext, useCallback, useContext, useLayoutEffect, useMemo} from 'react';
import {useLocation, useRouteMatch} from 'react-router-dom';
import {atom, useRecoilValue} from 'recoil';

export const currentPageAtom = atom<{path: string; specificPath: string}>({
  key: 'currentPageAtom',
  default: {path: '/', specificPath: '/'},
});

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
