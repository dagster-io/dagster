import {Box, Tooltip, UnstyledButton} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {Link} from 'react-router-dom';

import styles from './css/SideNavItem.module.css';

interface SideNavItemInterface {
  key: string;
  icon: React.ReactNode;
  label: React.ReactNode;
  disabled?: boolean;
  rightElement?: React.ReactNode;
  tooltip?: string;
  onClick?: () => void;
}

export interface SideNavItemLinkConfig extends SideNavItemInterface {
  type: 'link';
  path: string;
}

export interface SideNavItemButtonConfig extends SideNavItemInterface {
  type: 'button';
  onClick: () => void;
}

export type SideNavItemConfig = SideNavItemLinkConfig | SideNavItemButtonConfig;

interface Props {
  active?: boolean;
  item: SideNavItemConfig;
}

export const SideNavItem = (props: Props) => {
  const {active = false, item} = props;
  const {type, icon, label, rightElement, tooltip = '', disabled = false} = item;
  const content = (
    <Box
      padding={{vertical: 4, left: 12, right: 8}}
      flex={{direction: 'row', gap: 8, alignItems: 'center', justifyContent: 'space-between'}}
    >
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}} className="iconAndLabel">
        {icon}
        {label}
      </Box>
      <div>{rightElement}</div>
    </Box>
  );

  if (type === 'link' && !disabled) {
    return (
      <Tooltip canShow={!!tooltip} content={tooltip} placement="right" display="block">
        <Link
          to={item.path}
          className={clsx(styles.sideNavItem, active ? styles.active : styles.inactive)}
        >
          {content}
        </Link>
      </Tooltip>
    );
  }

  return (
    <Tooltip canShow={!!tooltip} content={tooltip} placement="right" display="block">
      <UnstyledButton
        className={clsx(styles.sideNavItem, active ? styles.active : styles.inactive)}
        disabled={disabled}
        onClick={item.onClick}
      >
        {content}
      </UnstyledButton>
    </Tooltip>
  );
};
