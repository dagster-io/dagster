import {useRouter} from 'next/router';
import {useState, useEffect} from 'react';

export const usePath = () => {
  const router = useRouter();

  const [asPath, setAsPath] = useState('/');

  useEffect(() => {
    if (router.isReady) {
      setAsPath(router.asPath);
    }
  }, [router]);

  let asPathWithoutAnchor = asPath;
  if (asPathWithoutAnchor.indexOf('#') > 0) {
    asPathWithoutAnchor = asPath.substring(0, asPath.indexOf('#'));
  }

  return {
    asPath,
    asPathWithoutAnchor,
  };
};
