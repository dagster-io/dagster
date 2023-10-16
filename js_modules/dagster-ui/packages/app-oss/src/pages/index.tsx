'use client';

import dynamic from 'next/dynamic';
import {useRouter} from 'next/router';
import React from 'react';

const App = dynamic(() => import('../App'), {
  ssr: false,
});

// eslint-disable-next-line import/no-default-export
export default function IndexPage() {
  const router = useRouter();

  React.useEffect(() => {
    router.beforePopState(() => {
      // Disable Next.js client side routing until we migrate to Next.js routing
      return false;
    });
  }, [router]);

  return (
    <div id="root">
      <App />
    </div>
  );
}

/**
 * Ignore hard navigation error (only happens in dev mode).
 */
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  const originalError = window.Error;
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  window.Error = function Error(...args) {
    if (args[0]?.includes('Invariant: attempted to hard navigate to the same URL')) {
      return;
    }
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    const err = originalError(...args);
    Object.setPrototypeOf(err, window.Error.prototype);
    return err;
  };
}
