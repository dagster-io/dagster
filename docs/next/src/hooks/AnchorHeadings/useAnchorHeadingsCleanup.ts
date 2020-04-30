import { useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import { useAnchorHeadingsActions } from '.';

const useAnchorHeadingsCleanup = () => {
  const { clearAnchorHeadings } = useAnchorHeadingsActions();
  const router = useRouter();

  const onClearAnchorHeadings = useCallback(() => {
    try {
      clearAnchorHeadings();
    } catch (error) {
      console.log('Attempting to clean up not initialized context.');
    }
  }, [clearAnchorHeadings]);

  useEffect(() => {
    router.events.on('routeChangeStart', onClearAnchorHeadings);
    return () => {
      router.events.off('routeChangeStart', onClearAnchorHeadings);
    };
  }, [router]);
};

export default useAnchorHeadingsCleanup;
