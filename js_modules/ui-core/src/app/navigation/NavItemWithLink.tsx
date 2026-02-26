import {Tooltip} from '@dagster-io/ui-components';
import {MatcherFn} from '@shared/app/AppTopNav/activePathMatchers';
import clsx from 'clsx';
import {ReactNode, useContext} from 'react';
import {NavLink} from 'react-router-dom';

import {NavCollapseContext} from './NavCollapseProvider';
import {NavItemContent} from './NavItemContent';
import styles from './css/MainNavigation.module.css';

interface Props {
  icon: ReactNode;
  href: string;
  label: string;
  isActive: MatcherFn;
  right?: ReactNode;
}

export const NavItemWithLink = ({icon, href, label, isActive}: Props) => {
  const {isCollapsed} = useContext(NavCollapseContext);

  return (
    <Tooltip content={label} placement="right" canShow={isCollapsed}>
      <NavLink
        to={href}
        isActive={isActive}
        className={(isActive) => clsx(styles.link, isActive ? styles.active : null)}
      >
        <NavItemContent icon={icon} label={label} collapsed={isCollapsed} />
      </NavLink>
    </Tooltip>
  );
};
