import {Tooltip} from '@dagster-io/ui-components';
import {ReactNode, useContext} from 'react';

import {NavCollapseContext} from './NavCollapseProvider';
import {NavItemContent} from './NavItemContent';
import styles from './css/MainNavigation.module.css';

interface Props {
  icon: ReactNode;
  label: string;
  tooltip?: string;
}

export const NavItemDisabled = ({icon, label, tooltip}: Props) => {
  const {isCollapsed} = useContext(NavCollapseContext);

  return (
    <Tooltip
      content={tooltip || label}
      canShow={isCollapsed || !!tooltip}
      placement={isCollapsed ? 'right' : 'bottom'}
    >
      <div className={styles.disabledItem}>
        <NavItemContent icon={icon} label={label} collapsed={isCollapsed} />
      </div>
    </Tooltip>
  );
};
