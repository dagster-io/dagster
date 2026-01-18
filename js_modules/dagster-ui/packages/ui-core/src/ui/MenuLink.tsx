import {
  CommonMenuItemProps,
  MenuExternalLink,
  MenuItem,
  MenuItemContents,
} from '@dagster-io/ui-components';
import {Link, LinkProps} from 'react-router-dom';

import styles from './css/MenuLink.module.css';

interface MenuLinkProps
  extends CommonMenuItemProps,
    Omit<
      React.ComponentProps<typeof MenuExternalLink>,
      'onClick' | 'onFocus' | 'target' | 'ref' | 'href' | 'download'
    >,
    LinkProps {
  disabled?: boolean;
}

/**
 * If you want to use a menu item as a link, use `MenuLink` and provide a `to` prop.
 */
export const MenuLink = (props: MenuLinkProps) => {
  const {icon, intent = 'none', disabled = false, text, to, ...rest} = props;

  if (disabled) {
    return <MenuItem icon={icon} text={text} disabled />;
  }

  return (
    <li role="none" className="popover-dismiss" style={{listStyle: 'none'}}>
      <Link {...rest} to={to} role="menuitem" tabIndex={0} className={styles.menuLink}>
        <MenuItemContents icon={icon} intent={intent} text={text} />
      </Link>
    </li>
  );
};
