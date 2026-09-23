import {
  ComponentProps,
  ReactElement,
  ReactNode,
  isValidElement,
  memo,
  useContext,
  useLayoutEffect,
  useMemo,
  useRef,
} from 'react';
import {Route as ReactRouterRoute, Redirect, useLocation, useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';

import {currentPageAtom} from './analytics';
import {useIsMobileLayout} from './layout/LayoutMode';
import {
  MobileRouteStatus,
  MobileRouteStatusContext,
  RouteDepthContext,
  useClaimMobileRouteStatus,
} from './layout/mobileRouteStatus';

type WrapperProps = {
  // How the route presents in mobile layout mode: an element rendered instead of the
  // desktop content, `'supported'` if the desktop content already works on mobile, or
  // `'unsupported'` to force the desktop fallback under a supported parent. Omit to
  // inherit from the enclosing route.
  mobile?: ReactElement | MobileRouteStatus;
  // Set to true if this route nests other routes below it.
  isNestingRoute?: boolean;
};

type Props = ComponentProps<typeof ReactRouterRoute> & WrapperProps;

export const Route = memo((props: Props) => {
  const {render, children, isNestingRoute, component: Component, mobile} = props;

  // Read through a ref so a fresh `mobile` element doesn't invalidate the memoized
  // component below, which would remount the route content on every parent render.
  const wrapperPropsRef = useRef<WrapperProps>({});
  wrapperPropsRef.current = {mobile, isNestingRoute};

  const renderFn = useMemo(() => {
    if (!render) {
      return;
    }
    return (...args: Parameters<typeof render>) => {
      return <Wrapper {...wrapperPropsRef.current}>{render(...args)}</Wrapper>;
    };
  }, [render]);
  const WrapperComponent = useMemo(() => {
    if (!Component) {
      return;
    }
    return (props: any) => (
      <Wrapper {...wrapperPropsRef.current}>
        <Component {...props} />
      </Wrapper>
    );
  }, [Component]);

  const childRenderFn = useMemo(() => {
    if (!(children instanceof Function)) {
      return;
    }
    return (...args: Parameters<typeof children>) => (
      <Wrapper {...wrapperPropsRef.current}>{children(...args)}</Wrapper>
    );
  }, [children]);

  if (render) {
    return <ReactRouterRoute {...props} render={renderFn} />;
  }
  if (Component) {
    return <ReactRouterRoute {...props} component={WrapperComponent} />;
  }
  if (children instanceof Function) {
    return <ReactRouterRoute {...props}>{childRenderFn}</ReactRouterRoute>;
  }
  return (
    <ReactRouterRoute {...props}>
      <Wrapper mobile={mobile} isNestingRoute={isNestingRoute}>
        {children}
      </Wrapper>
    </ReactRouterRoute>
  );
});

const Wrapper = memo(({children, isNestingRoute, mobile}: WrapperProps & {children: ReactNode}) => {
  const {path} = useRouteMatch();
  const {pathname} = useLocation();
  const isMobile = useIsMobileLayout();

  const inherited = useContext(MobileRouteStatusContext);
  const depth = useContext(RouteDepthContext) + 1;

  let status: MobileRouteStatus = inherited;
  let content: ReactNode = children;
  if (isValidElement(mobile)) {
    status = 'supported';
    if (isMobile) {
      content = mobile;
    }
  } else if (typeof mobile === 'string') {
    status = mobile;
  }

  // Redirects are transient; reporting them would flip the layout for one commit.
  const isRedirect = isValidElement(content) && content.type === Redirect;

  const setCurrentPage = useSetRecoilState(currentPageAtom);
  const claimStatus = useClaimMobileRouteStatus();
  useLayoutEffect(() => {
    if (path !== '*' && !isNestingRoute && !isRedirect) {
      setCurrentPage(({specificPath}) => ({specificPath, path}));
      claimStatus({pathname, depth, status});
    }
  }, [path, pathname, depth, isNestingRoute, isRedirect, status, setCurrentPage, claimStatus]);

  return (
    <RouteDepthContext.Provider value={depth}>
      <MobileRouteStatusContext.Provider value={status}>
        {content}
      </MobileRouteStatusContext.Provider>
    </RouteDepthContext.Provider>
  );
});
