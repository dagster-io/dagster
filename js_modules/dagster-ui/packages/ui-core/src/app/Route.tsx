import {ComponentProps, ReactNode, memo, useLayoutEffect, useMemo} from 'react';
import {Route as ReactRouterRoute, useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';

import {currentPageAtom} from './analytics';

type Props = ComponentProps<typeof ReactRouterRoute> & {
  // Set to true if this route nests other routes below it.
  isNestingRoute?: boolean;
};

export const Route = memo((props: Props) => {
  const {render, children, isNestingRoute, component: Component} = props;

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
      <Wrapper isNestingRoute={isNestingRoute}>{children}</Wrapper>
    </ReactRouterRoute>
  );
});

const Wrapper = memo(
  ({children, isNestingRoute}: {children: ReactNode; isNestingRoute?: boolean}) => {
    const {path} = useRouteMatch();

    const setCurrentPage = useSetRecoilState(currentPageAtom);
    useLayoutEffect(() => {
      if (path !== '*' && !isNestingRoute) {
        setCurrentPage(({specificPath}) => ({specificPath, path}));
      }
    }, [path, isNestingRoute, setCurrentPage]);

    return children;
  },
);
