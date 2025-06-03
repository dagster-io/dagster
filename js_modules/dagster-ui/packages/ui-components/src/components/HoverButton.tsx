import {ComponentProps} from 'react';

import {UnstyledButton} from './UnstyledButton';
import styles from './css/HoverButton.module.css';

export const HoverButton = (props: ComponentProps<typeof UnstyledButton>) => {
  return <UnstyledButton {...props} className={styles.button} />;
};
