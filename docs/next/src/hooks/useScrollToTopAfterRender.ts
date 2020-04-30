import { useCallback, useEffect } from 'react';
import { useRouter } from 'next/router';

const useScrollToTopAfterRender = () => {
  const router = useRouter();

  const scrollToTop = useCallback(() => window.scrollTo(0, 0), [router]);

  useEffect(() => {
    router.events.on('routeChangeComplete', scrollToTop);
    return () => {
      router.events.off('routeChangeComplete', scrollToTop);
    };
  }, [router]);
};

export default useScrollToTopAfterRender;
