import {createContext, useCallback, useContext, useLayoutEffect} from 'react';
import {useLocation} from 'react-router-dom';
import {atom, useRecoilValue, useSetRecoilState} from 'recoil';

import {useIsMobileLayout} from './LayoutMode';

/**
 * Whether the currently rendered page has a mobile-friendly presentation.
 *
 * Every matched `Route` reports its status for the current pathname. Layout effects run
 * child-first, so a plain "last write wins" would let an unannotated outer route overwrite
 * its leaf; instead each write carries its depth and a shallower write for the same
 * pathname is rejected. A pathname the claim doesn't match (e.g. a tree of `path="*"`
 * routes that never report) reads as `unsupported`.
 */
export type MobileRouteStatus = 'supported' | 'unsupported';

type Claim = {pathname: string; depth: number; status: MobileRouteStatus};

export const mobileRouteStatusAtom = atom<Claim | null>({
  key: 'mobileRouteStatusAtom',
  default: null,
});

// Unannotated routes inherit from the nearest annotated ancestor.
export const MobileRouteStatusContext = createContext<MobileRouteStatus>('unsupported');

// Nesting depth of the enclosing `Route`; deeper claims win.
export const RouteDepthContext = createContext(0);

export const useMobileRouteStatus = (): MobileRouteStatus => {
  const claim = useRecoilValue(mobileRouteStatusAtom);
  const {pathname} = useLocation();
  return claim?.pathname === pathname ? claim.status : 'unsupported';
};

// Whether the mobile layout should be in use: layout mode is mobile and the current route
// claims support. For the navigation and providers; pages read `useIsMobile` instead.
export const useMobileRouteEnabled = () => {
  const isMobile = useIsMobileLayout();
  const status = useMobileRouteStatus();
  return isMobile && status === 'supported';
};

export const useClaimMobileRouteStatus = () => {
  const setClaim = useSetRecoilState(mobileRouteStatusAtom);
  return useCallback(
    (claim: Claim) => {
      setClaim((prev) =>
        prev && prev.pathname === claim.pathname && prev.depth > claim.depth ? prev : claim,
      );
    },
    [setClaim],
  );
};

// What the enclosing `Route` renders, so a lazily-loaded component can tell whether it's the
// route's content or a widget inside it.
export const RouteContentContext = createContext<{type: unknown; pathname: string} | null>(null);

/**
 * While a route's content is still loading, its status is unknown: the routes inside it that
 * declare it haven't mounted, and the enclosing route's status is usually just inherited.
 * Keep the previous page's layout until they report (the content is blank meanwhile), then
 * fall back to the enclosing route's status if nothing inside claims one.
 */
export const useUnknownMobileRouteStatus = (isUnknown: boolean, pathname: string | undefined) => {
  const setClaim = useSetRecoilState(mobileRouteStatusAtom);
  const depth = useContext(RouteDepthContext);
  const inherited = useContext(MobileRouteStatusContext);
  useLayoutEffect(() => {
    if (!isUnknown || !pathname) {
      return;
    }
    let placeholder: Claim | null = null;
    setClaim((prev) => {
      if (!prev || prev.pathname === pathname) {
        return prev;
      }
      placeholder = {pathname, depth: depth + 1, status: prev.status};
      return placeholder;
    });
    return () => {
      setClaim((prev) => (prev === placeholder ? {pathname, depth, status: inherited} : prev));
    };
  }, [isUnknown, pathname, depth, inherited, setClaim]);
};

/**
 * Declare the status from inside a page component, for pages whose mobile-friendliness
 * depends on state the route can't see (e.g. a `?view=` tab). Wins over the enclosing
 * route's annotation.
 */
export const useDeclareMobileRouteStatus = (status: MobileRouteStatus) => {
  const claimStatus = useClaimMobileRouteStatus();
  const depth = useContext(RouteDepthContext);
  const {pathname} = useLocation();
  useLayoutEffect(() => {
    claimStatus({pathname, depth: depth + 1, status});
  }, [claimStatus, pathname, depth, status]);
};
