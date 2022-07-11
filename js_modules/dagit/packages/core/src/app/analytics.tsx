import * as React from 'react';
import {useLocation, useRouteMatch} from 'react-router-dom';

export interface GenericAnalytics {
  group?: (groupId: string, traits: Record<string, any>) => void;
  identify?: (userId: string) => void;
  page: (path: string, specificPath: string) => void;
  track: (eventName: string, properties?: Record<string, any>) => void;
}

export const AnalyticsContext = React.createContext<GenericAnalytics>(undefined!);

const PAGEVIEW_DELAY = 300;

const usePageContext = () => {
  const match = useRouteMatch();
  const {pathname: specificPath} = useLocation();
  const {path} = match;
  return React.useMemo(() => ({path, specificPath}), [path, specificPath]);
};

const useAnalytics = () => {
  const analytics = React.useContext(AnalyticsContext);
  if (!analytics) {
    throw new Error('Analytics may only be used within `AnalyticsContext.Provider`.');
  }
  return analytics;
};

export const dummyAnalytics = () => ({
  group: (groupId: string, traits: Record<string, any>) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Group]', groupId, traits);
    }
  },
  identify: (id: string) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Identify]', id);
    }
  },
  page: (path: string, specificPath: string) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Pageview]', {path, specificPath});
    }
  },
  track: (eventName: string, properties?: Record<string, any>) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Event]', eventName, properties);
    }
  },
});

export const useTrackPageView = () => {
  const analytics = useAnalytics();
  const {path, specificPath} = usePageContext();

  React.useEffect(() => {
    // Wait briefly to allow redirects.
    const timer = setTimeout(() => {
      analytics.page(path, specificPath);
    }, PAGEVIEW_DELAY);

    return () => {
      clearTimeout(timer);
    };
  }, [analytics, path, specificPath]);
};

export const useTrackEvent = () => {
  const analytics = useAnalytics();
  const pathValues = usePageContext();

  return React.useCallback(
    (eventName: string, properties?: Record<string, any>) => {
      analytics.track(eventName, {...properties, ...pathValues});
    },
    [analytics, pathValues],
  );
};
