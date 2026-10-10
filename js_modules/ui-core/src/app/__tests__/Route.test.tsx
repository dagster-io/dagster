import {act, render, screen} from '@testing-library/react';
import {MemoryRouter, Redirect, Switch, useHistory} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {lazy} from '../../util/lazy';
import {Route} from '../Route';
import {LayoutMode} from '../layout/LayoutMode';
import {LayoutModeProvider} from '../layout/LayoutModeProvider';
import {
  MobileRouteStatus,
  useDeclareMobileRouteStatus,
  useMobileRouteStatus,
} from '../layout/mobileRouteStatus';

const Status = () => <div data-testid="status">{useMobileRouteStatus()}</div>;

let history: ReturnType<typeof useHistory> | null = null;
const CaptureHistory = () => {
  history = useHistory();
  return null;
};

const renderAt = (mode: LayoutMode, path: string, routes: React.ReactNode) =>
  render(
    <RecoilRoot>
      <LayoutModeProvider mode={mode}>
        <MemoryRouter initialEntries={[path]}>
          <CaptureHistory />
          <Status />
          <Switch>{routes}</Switch>
        </MemoryRouter>
      </LayoutModeProvider>
    </RecoilRoot>,
  );

const navigate = (path: string) => {
  act(() => {
    history?.push(path);
  });
};

const status = () => screen.getByTestId('status').textContent as MobileRouteStatus;

// A `lazy` component whose import resolves when `load` is called.
const deferredLazy = (Component: React.ComponentType) => {
  let resolve: (value: {default: React.ComponentType}) => void = () => {};
  const promise = new Promise<{default: React.ComponentType}>((r) => (resolve = r));
  const load = async () => {
    await act(async () => {
      resolve({default: Component});
      await promise;
    });
  };
  return {Lazy: lazy(() => promise), load};
};

describe('Route', () => {
  describe('mobile variants', () => {
    const routes = (
      <Route path="/runs" mobile={<div>mobile runs</div>}>
        <div>desktop runs</div>
      </Route>
    );

    it('renders the desktop content in desktop mode', () => {
      renderAt('desktop', '/runs', routes);
      expect(screen.getByText('desktop runs')).toBeVisible();
      expect(screen.queryByText('mobile runs')).toBeNull();
      // Desktop mode never enters the mobile layout, but the status still reflects the route.
      expect(status()).toBe('supported');
    });

    it('renders the mobile element in mobile mode', () => {
      renderAt('mobile', '/runs', routes);
      expect(screen.getByText('mobile runs')).toBeVisible();
      expect(screen.queryByText('desktop runs')).toBeNull();
      expect(status()).toBe('supported');
    });

    it('supports the render form', () => {
      renderAt(
        'mobile',
        '/runs',
        <Route path="/runs" mobile={<div>mobile</div>} render={() => <div>desktop</div>} />,
      );
      expect(screen.getByText('mobile')).toBeVisible();
      expect(screen.queryByText('desktop')).toBeNull();
    });

    it('supports the component form', () => {
      const Desktop = () => <div>desktop component</div>;
      renderAt(
        'mobile',
        '/runs',
        <Route path="/runs" mobile={<div>mobile</div>} component={Desktop} />,
      );
      expect(screen.getByText('mobile')).toBeVisible();
    });

    it('treats mobile="unsupported" as explicitly desktop-only', () => {
      renderAt(
        'mobile',
        '/graph',
        <Route path="/graph" mobile="unsupported">
          <div>graph</div>
        </Route>,
      );
      expect(screen.getByText('graph')).toBeVisible();
      expect(status()).toBe('unsupported');
    });
  });

  describe('mobile route status', () => {
    it('reports unsupported for an unannotated route', () => {
      renderAt(
        'mobile',
        '/graph',
        <Route path="/graph">
          <div>graph</div>
        </Route>,
      );
      expect(status()).toBe('unsupported');
    });

    it('reports supported for a mobile="supported" route', () => {
      renderAt(
        'mobile',
        '/automation',
        <Route path="/automation" mobile="supported">
          <div>automation</div>
        </Route>,
      );
      expect(screen.getByText('automation')).toBeVisible();
      expect(status()).toBe('supported');
    });

    it('lets unannotated inner routes inherit from an annotated outer route', () => {
      renderAt(
        'mobile',
        '/assets/foo',
        <Route path="/assets" mobile="supported" isNestingRoute>
          <Switch>
            <Route path="/assets/:name">
              <div>asset tab</div>
            </Route>
          </Switch>
        </Route>,
      );
      expect(screen.getByText('asset tab')).toBeVisible();
      expect(status()).toBe('supported');
    });

    it('lets an inner route opt out of an annotated outer route', () => {
      renderAt(
        'mobile',
        '/deployment/admin',
        <Route path="/deployment" mobile="supported" isNestingRoute>
          <Switch>
            <Route path="/deployment/admin" mobile="unsupported">
              <div>admin</div>
            </Route>
          </Switch>
        </Route>,
      );
      expect(status()).toBe('unsupported');
    });

    it('lets the innermost route win regardless of effect order', () => {
      // The outer route is not marked as nesting, so it reports too. Its layout effect
      // runs after the inner one, and must not overwrite the inner claim.
      renderAt(
        'mobile',
        '/deployment/locations',
        <Route path="/deployment">
          <Switch>
            <Route path="/deployment/locations" mobile="supported">
              <div>locations</div>
            </Route>
            <Route path="/deployment/config">
              <div>config</div>
            </Route>
          </Switch>
        </Route>,
      );
      expect(status()).toBe('supported');

      navigate('/deployment/config');
      expect(status()).toBe('unsupported');

      navigate('/deployment/locations');
      expect(status()).toBe('supported');
    });

    it('reports unsupported on a page whose only routes are catch-alls', () => {
      renderAt(
        'mobile',
        '/runs',
        <>
          <Route path="/runs" mobile="supported">
            <div>runs</div>
          </Route>
          <Route path="*" isNestingRoute>
            <div>not found</div>
          </Route>
        </>,
      );
      expect(status()).toBe('supported');

      navigate('/nope');
      expect(screen.getByText('not found')).toBeVisible();
      expect(status()).toBe('unsupported');
    });

    it('does not report redirect routes', () => {
      renderAt(
        'mobile',
        '/',
        <>
          <Route path="/" exact render={() => <Redirect to="/home" />} />
          <Route path="/home" mobile="supported">
            <div>home</div>
          </Route>
        </>,
      );
      expect(screen.getByText('home')).toBeVisible();
      expect(status()).toBe('supported');
    });

    it('lets a page component declare its own status', () => {
      const Page = ({tab}: {tab: string}) => {
        useDeclareMobileRouteStatus(tab === 'events' ? 'supported' : 'unsupported');
        return <div>{tab}</div>;
      };
      renderAt(
        'mobile',
        '/asset?view=events',
        <Route
          path="/asset"
          mobile="supported"
          render={({location}) => (
            <Page tab={new URLSearchParams(location.search).get('view') ?? ''} />
          )}
        />,
      );
      expect(screen.getByText('events')).toBeVisible();
      expect(status()).toBe('supported');

      navigate('/asset?view=lineage');
      expect(screen.getByText('lineage')).toBeVisible();
      expect(status()).toBe('unsupported');
    });
  });

  describe('lazily-loaded route content', () => {
    it('keeps the previous status until the routes inside it report', async () => {
      const {Lazy: IssuesRoot, load} = deferredLazy(() => (
        <Switch>
          <Route path="/issues" exact mobile="supported">
            <div>issues</div>
          </Route>
        </Switch>
      ));
      renderAt(
        'mobile',
        '/runs',
        <>
          <Route path="/runs" mobile="unsupported">
            <div>runs</div>
          </Route>
          <Route path="/home" mobile="supported">
            <div>home</div>
          </Route>
          <Route path="/issues">
            <IssuesRoot />
          </Route>
        </>,
      );
      navigate('/home');
      expect(status()).toBe('supported');

      // Not "unsupported", which the unannotated outer route inherits.
      navigate('/issues');
      expect(status()).toBe('supported');

      await load();
      expect(screen.getByText('issues')).toBeVisible();
      expect(status()).toBe('supported');
    });

    it('falls back to the enclosing route once loaded if nothing inside reports', async () => {
      const {Lazy: SettingsRoot, load} = deferredLazy(() => <div>settings</div>);
      renderAt(
        'mobile',
        '/home',
        <>
          <Route path="/home" mobile="supported">
            <div>home</div>
          </Route>
          <Route path="/settings">
            <SettingsRoot />
          </Route>
        </>,
      );
      navigate('/settings');
      expect(status()).toBe('supported');

      await load();
      expect(screen.getByText('settings')).toBeVisible();
      expect(status()).toBe('unsupported');
    });

    it('does not hold the status for a lazy component inside the page', async () => {
      const {Lazy: Widget, load} = deferredLazy(() => <div>widget</div>);
      renderAt(
        'mobile',
        '/home',
        <>
          <Route path="/home" mobile="supported">
            <div>home</div>
          </Route>
          <Route path="/settings">
            <div>
              <Widget />
            </div>
          </Route>
        </>,
      );
      navigate('/settings');
      expect(status()).toBe('unsupported');
      await load();
      expect(status()).toBe('unsupported');
    });

    it('renders synchronously on later mounts', async () => {
      const {Lazy: Page, load} = deferredLazy(() => <div>page</div>);
      renderAt(
        'mobile',
        '/page',
        <>
          <Route path="/page">
            <Page />
          </Route>
          <Route path="/other">
            <div>other</div>
          </Route>
        </>,
      );
      await load();
      navigate('/other');
      navigate('/page');
      expect(screen.getByText('page')).toBeVisible();
    });
  });
});
