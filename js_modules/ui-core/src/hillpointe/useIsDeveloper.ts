import {useEffect, useState} from 'react';

// Who may see the developer settings, as SHA-256 hashes of lowercase sign-in
// emails. Hashes, because this repository is public. To add someone, run
//   printf '%s' 'name@example.com' | sha256sum
// and add the result here.
const DEVELOPER_EMAIL_HASHES = new Set([
  'b6b6fbb98c77846b672f60d59d1bf9db36e56a65f2e47f6debf7f1020200905a',
  '87f4d56f07ed668da3b365dadfd31b5ce8aea4edcbc7f878f05f098a7b775183',
  // The shared account the TV screens sign in with.
  '4afe39326a8cfea23777417a54fe77f274b7d5ccd900e732d3bba6f642247b92',
]);

// oauth2-proxy, which sits in front of the site, reports the signed-in user here.
const USERINFO_URL = '/oauth2/userinfo';

const sha256 = async (text: string) => {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
};

/**
 * Whether the signed-in user is on the developer list. Always true in local
 * development, where there is no sign-in. This only hides settings; it is not
 * a security boundary.
 */
export const useIsDeveloper = () => {
  const [isDeveloper, setIsDeveloper] = useState(process.env.NODE_ENV === 'development');
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(USERINFO_URL, {cache: 'no-store'});
        const email = res.ok ? (await res.json()).email : null;
        if (typeof email !== 'string') {
          return;
        }
        const allowed = DEVELOPER_EMAIL_HASHES.has(await sha256(email.trim().toLowerCase()));
        if (!cancelled) {
          setIsDeveloper(allowed);
        }
      } catch {
        // Not signed in through the proxy, or it is unreachable: stay hidden.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);
  return isDeveloper;
};
