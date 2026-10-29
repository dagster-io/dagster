import {
  Box,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Tab,
  Tabs,
  Tooltip,
  UnstyledButton,
} from '@dagster-io/ui-components';
import {ReactNode, useState} from 'react';

import {MenuLink} from './MenuLink';
import {TabLink} from './TabLink';
import styles from './css/RouteTabs.module.css';
import {useIsMobile} from '../app/layout/IsMobileContext';

export type RouteTabConfig = {
  id: string;
  title: ReactNode;
  to: string;
  icon?: ReactNode;
  disabled?: boolean;
  // Explains why a disabled tab is disabled.
  tooltip?: ReactNode;
  hidden?: boolean;
  // Whether the destination has a mobile layout. Others are labeled "Desktop" in the mobile
  // picker, since opening them leaves the mobile layout.
  mobile?: boolean;
};

interface Props {
  selectedTabId: string;
  tabs: RouteTabConfig[];
}

/**
 * A row of tabs that link to routes. In the mobile layout the row becomes a picker that opens
 * the same tabs as a menu, so every tab bar built from this gets a mobile version for free.
 */
export const RouteTabs = ({selectedTabId, tabs}: Props) => {
  const isMobile = useIsMobile();
  const visibleTabs = tabs.filter((tab) => !tab.hidden);

  if (isMobile) {
    return <RouteTabPicker selectedTabId={selectedTabId} tabs={visibleTabs} />;
  }

  return (
    <Tabs selectedTabId={selectedTabId}>
      {visibleTabs.map(({id, title, to, icon, tooltip, disabled}) =>
        disabled ? (
          <Tab
            disabled
            key={id}
            id={id}
            icon={icon}
            title={
              <Tooltip content={tooltip || ''} canShow={!!tooltip} placement="top">
                {title}
              </Tooltip>
            }
          />
        ) : (
          <TabLink key={id} id={id} title={title} to={to} icon={icon} />
        ),
      )}
    </Tabs>
  );
};

/**
 * The tab row doesn't fit on a phone, and a horizontally scrolling row hides most of it.
 * The tabs become a full-width control that opens the same list as a menu instead.
 */
const RouteTabPicker = ({selectedTabId, tabs}: Props) => {
  const [isOpen, setIsOpen] = useState(false);

  if (tabs.length === 0) {
    return null;
  }
  const selected = tabs.find((tab) => tab.id === selectedTabId) ?? tabs[0];

  return (
    <Popover
      fill
      matchTargetWidth
      className={styles.pickerTarget}
      placement="bottom-start"
      isOpen={isOpen}
      onInteraction={(nextOpen) => setIsOpen(nextOpen)}
      content={
        <Menu>
          {tabs.map(({id, title, to, tooltip, disabled, mobile}) => {
            const text = mobile ? (
              title
            ) : (
              <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 8}}>
                {title}
                <span className={styles.desktopLabel}>[Desktop]</span>
              </Box>
            );
            return disabled ? (
              <MenuItem
                key={id}
                // Tooltips don't open on touch, so the reason is shown inline.
                text={
                  tooltip ? (
                    <Box flex={{direction: 'column', gap: 2}}>
                      {text}
                      <span className={styles.disabledReason}>{tooltip}</span>
                    </Box>
                  ) : (
                    text
                  )
                }
                disabled
              />
            ) : (
              <MenuLink
                key={id}
                to={to}
                text={text}
                active={id === selectedTabId}
                onClick={() => setIsOpen(false)}
              />
            );
          })}
        </Menu>
      }
    >
      <UnstyledButton
        type="button"
        className={styles.picker}
        aria-haspopup="menu"
        aria-expanded={isOpen}
      >
        <span>{selected?.title}</span>
        <Icon name="arrow_drop_down" />
      </UnstyledButton>
    </Popover>
  );
};
