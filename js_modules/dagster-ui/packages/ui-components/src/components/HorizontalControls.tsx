import {ReactNode} from 'react';

import {Box} from './Box';
import styles from './css/HorizontalControls.module.css';

type Control = {key: string; control: ReactNode};

interface Props {
  controls: Control[];
}

export const HorizontalControls = ({controls}: Props) => {
  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}} className={styles.container}>
      {controls.map(({key, control}) =>
        control ? (
          <div key={key} className={styles.item}>
            {control}
          </div>
        ) : null,
      )}
    </Box>
  );
};
