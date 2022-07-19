import React from 'react';

// This might not be necessary soon - creating this shared hook so we can find all usages
// easily later.

export function useIsMounted() {
  const mounted = React.useRef<boolean>(false);
  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  return mounted;
}
