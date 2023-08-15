import * as React from 'react';

export const useFavicon = (href: string) => {
  React.useEffect(() => {
    const el = document.querySelector('link[rel="icon"][type="image/svg+xml"]');
    if (!el) {
      return;
    }
    const previousHref = el.getAttribute('href');
    el.setAttribute('href', href);
    return () => {
      if (previousHref) {
        el.setAttribute('href', previousHref);
      }
    };
  }, [href]);
};
