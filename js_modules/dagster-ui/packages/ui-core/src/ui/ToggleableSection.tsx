import {Box, Colors, Icon} from '@dagster-io/ui-components';
import * as React from 'react';
import clsx from 'clsx';
import styles from './ToggleableSection.module.css';

export const ToggleableSection = ({
  isInitiallyOpen,
  title,
  children,
  background,
}: {
  isInitiallyOpen: boolean;
  title: React.ReactNode;
  children: React.ReactNode;
  background?: string;
}) => {
  const [isOpen, setIsOpen] = React.useState(isInitiallyOpen);
  return (
    <Box>
      <Box
        onClick={() => setIsOpen(!isOpen)}
        background={background ?? Colors.backgroundLight()}
        border="bottom"
        flex={{alignItems: 'center', direction: 'row'}}
        padding={{vertical: 12, right: 20, left: 16}}
        style={{cursor: 'pointer'}}
      >
        <span className={clsx(styles.rotateable, !isOpen ? styles.rotated : null)}>
          <Icon name="arrow_drop_down" />
        </span>
        <div style={{flex: 1}}>{title}</div>
      </Box>
      {isOpen && <Box>{children}</Box>}
    </Box>
  );
};
