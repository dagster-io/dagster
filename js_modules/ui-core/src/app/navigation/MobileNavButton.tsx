import {Button, Icon} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {LayoutContext} from '../LayoutProvider';
import styles from './css/MobileNavButton.module.css';

/**
 * Opens the nav drawer. Floats over the top-left corner of the page rather than living in
 * a bar of its own, so pages keep their full height; mobile-ready pages leave that corner
 * clear (see `--mobile-nav-button-inset-*`).
 */
export const MobileNavButton = () => {
  const {nav} = useContext(LayoutContext);
  return (
    <div className={styles.container}>
      <Button icon={<Icon name="menu" />} onClick={nav.open} aria-label="Open navigation" />
    </div>
  );
};
