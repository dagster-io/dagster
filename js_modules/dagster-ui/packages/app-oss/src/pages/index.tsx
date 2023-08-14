'use client';

import dynamic from 'next/dynamic';
import {useRouter} from 'next/router';
import React from 'react';

const App = dynamic(
  () =>
    import('../App')
      .then((res) => {
        console.log(res);
        return res;
      })
      .catch((...args) => {
        console.log(args);
        return args[0];
      }),
  {
    ssr: false,
  },
);

// eslint-disable-next-line import/no-default-export
export default function IndexPage() {
  const router = useRouter();

  React.useEffect(() => {
    router.beforePopState(() => {
      console.log('returning false');
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
