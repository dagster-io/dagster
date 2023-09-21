import {registerPortalProvider} from '@dagster-io/ui-components/src/components/createToaster';
import React from 'react';
import ReactDOM from 'react-dom';
import {useHref} from 'react-router-dom-v5-compat';

// A hook that makes toaster elements render inside of our React router Provider and that fixes their hrefs
// to take --path-prefix into account
export const AppToasterPortalProvider = () => {
  const [portaledElements, setPortalElements] = React.useState<
    [React.ReactNode, HTMLElement, string | undefined][]
  >([]);
  const baseHref = useHref('');
  React.useLayoutEffect(() => {
    registerPortalProvider((node, container, key) => {
      setPortalElements((elements) => {
        return [...elements, [node, container, key]];
      });
    }, baseHref);
  }, [baseHref]);

  return (
    <>
      {portaledElements.map(([node, container, key], index) =>
        ReactDOM.createPortal(node, container, key ?? String(index)),
      )}
    </>
  );
};
