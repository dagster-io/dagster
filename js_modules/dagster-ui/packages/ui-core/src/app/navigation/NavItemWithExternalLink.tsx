import {Tooltip} from '@dagster-io/ui-components';
import {ReactNode, useContext} from 'react';

import {NavCollapseContext} from './NavCollapseProvider';
import {NavItemContent} from './NavItemContent';
import styles from './css/MainNavigation.module.css';

interface NavItemWithExternalLinkProps {
  icon: ReactNode;
  href: string;
  label: string;
}

export const NavItemWithExternalLink = ({icon, href, label}: NavItemWithExternalLinkProps) => {
  const {isCollapsed} = useContext(NavCollapseContext);

  return (
    <Tooltip content={label} placement="right" canShow={isCollapsed}>
      <a href={href} target="_blank" rel="noreferrer" className={styles.link}>
        <NavItemContent icon={icon} label={label} collapsed={isCollapsed} />
      </a>
    </Tooltip>
  );
};
