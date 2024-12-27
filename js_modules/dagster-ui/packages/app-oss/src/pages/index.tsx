'use client';

import dynamic from 'next/dynamic';
import {useRouter} from 'next/router';
import {useEffect} from 'react';

const App = dynamic(() => import('../App'), {
  ssr: false,
});

// eslint-disable-next-line import/no-default-export
export default function IndexPage() {
  const router = useRouter();

  useEffect(() => {
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
