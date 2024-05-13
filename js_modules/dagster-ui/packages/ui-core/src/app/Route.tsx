import {ComponentProps, ReactNode, memo, useLayoutEffect, useMemo} from 'react';
import {Route as ReactRouterRoute, useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';

import {currentPageAtom} from './analytics';

export const Route = memo((props: ComponentProps<typeof ReactRouterRoute>) => {
  const {render, children, component: Component} = props;

  const renderFn = useMemo(() => {
    if (!render) {
      return;
    }
    return (...args: Parameters<typeof render>) => {
      return <Wrapper>{render(...args)}</Wrapper>;
    };
  }, [render]);
  const WrapperComponent = useMemo(() => {
    if (!Component) {
      return;
    }
    return (props: any) => (
      <Wrapper>
        <Component {...props} />
      </Wrapper>
    );
  }, [Component]);

  const childRenderFn = useMemo(() => {
    if (!(children instanceof Function)) {
      return;
    }
    return (...args: Parameters<typeof children>) => <Wrapper>{children(...args)}</Wrapper>;
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
      <Wrapper>{children}</Wrapper>
    </ReactRouterRoute>
  );
});

const Wrapper = memo(({children}: {children: ReactNode}) => {
  const {path} = useRouteMatch();

  const setCurrentPage = useSetRecoilState(currentPageAtom);
  useLayoutEffect(() => {
    setCurrentPage(({specificPath}) => ({specificPath, path}));
  }, [path, setCurrentPage]);

  return children;
});
