import {useEffect} from 'react';

export const useFavicon = (href: string) => {
  useEffect(() => {
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
