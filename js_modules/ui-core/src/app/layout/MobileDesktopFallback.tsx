import {ButtonLink} from '@dagster-io/ui-components';
import {useState} from 'react';

import styles from './css/MobileDesktopFallback.module.css';
import {usePreferDesktopSite} from '../UserSettingsDialog/usePreferDesktopSite';

/**
 * Shown on a phone when the current route has no mobile presentation. The page renders at
 * desktop width and the browser zooms out, so this is sized in `vw` to stay legible.
 */
export const MobileDesktopFallbackBanner = () => {
  const [dismissed, setDismissed] = useState(false);
  const {setPreferDesktopSite} = usePreferDesktopSite();
  if (dismissed) {
    return null;
  }

  return (
    <div className={styles.banner} role="status">
      <span>This page isn’t optimized for mobile yet.</span>
      <ButtonLink
        underline="always"
        onClick={() => {
          setPreferDesktopSite(true);
          window.location.reload();
        }}
      >
        Always use the desktop site
      </ButtonLink>
      <ButtonLink underline="always" onClick={() => setDismissed(true)}>
        Dismiss
      </ButtonLink>
    </div>
  );
};
