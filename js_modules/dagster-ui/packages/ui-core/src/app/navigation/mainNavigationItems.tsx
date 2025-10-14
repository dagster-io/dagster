import {Icon, Popover, Tooltip, UnstyledButton} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';
import {
  assetsPathMatcher,
  automationPathMatcher,
  deploymentPathMatcher,
  jobsPathMatcher,
  lineagePathMatcher,
} from 'shared/app/AppTopNav/activePathMatchers.oss';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {useVisibleFeatureFlagRows} from 'shared/app/useVisibleFeatureFlagRows.oss';

import {ShortcutHandler} from '../ShortcutHandler';
import styles from './css/MainNavigation.module.css';
import {useSearchDialog} from '../../search/SearchDialog';
import {JobStateForNav} from '../AppTopNav/useJobStateForNav';
import {HelpMenuContents} from '../HelpMenu';
import {NavCollapseContext} from './NavCollapseProvider';
import {NavItemContent} from './NavItemContent';
import {NavItemWithLink} from './NavItemWithLink';
import {NavigationGroup} from './types';
import {UserSettingsDialog} from '../UserSettingsDialog/UserSettingsDialog';

type NavigationGroupConfig = {
  featureFlags: Record<FeatureFlag, boolean>;
  jobState: JobStateForNav;
};

const onlyAltKey = (event: KeyboardEvent) => {
  return event.altKey && !event.shiftKey && !event.ctrlKey && !event.metaKey;
};

const onlyCommandKey = (event: KeyboardEvent) => {
  return event.metaKey && !event.shiftKey && !event.ctrlKey && !event.altKey;
};

export const getTopGroups = (config: NavigationGroupConfig): NavigationGroup[] => {
  const {jobState} = config;
  return [
    {
      key: 'runs',
      items: [
        {
          key: 'overview',
          label: 'Overview',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyO',
            label: '⌥O',
            path: '/overview',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="timeline" />}
              label="Overview"
              href="/overview"
              isActive={(_, currentLocation) => currentLocation.pathname === '/overview'}
            />
          ),
        },
        {
          key: 'runs',
          label: 'Runs',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyR',
            label: '⌥R',
            path: '/runs',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="runs" />}
              label="Runs"
              href="/runs"
              isActive={(_, currentLocation) => currentLocation.pathname.startsWith('/runs')}
            />
          ),
        },
      ],
    },
    {
      key: 'observe',
      items: [
        {
          key: 'catalog',
          label: 'Catalog',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyC',
            label: '⌥C',
            path: '/assets',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="catalog_book" />}
              label="Catalog"
              href="/assets"
              isActive={assetsPathMatcher}
            />
          ),
        },
        jobState === 'has-jobs'
          ? {
              key: 'jobs',
              label: 'Jobs',
              shortcut: {
                filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyJ',
                label: '⌥J',
                path: '/jobs',
              },
              element: (
                <NavItemWithLink
                  icon={<Icon name="column_lineage" />}
                  label="Jobs"
                  href="/jobs"
                  isActive={jobsPathMatcher}
                />
              ),
            }
          : null,
        {
          key: 'automation',
          label: 'Automation',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyA',
            label: '⌥A',
            path: '/automation',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="schedule" />}
              label="Automation"
              href="/automation"
              isActive={(params, currentLocation) => {
                return (
                  automationPathMatcher(params, currentLocation) ||
                  // Special-case old Auto-materalize page, since with the new navigation we
                  // no longer have an "Overview" item to highlight.
                  currentLocation.pathname.startsWith('/overview/automation')
                );
              }}
            />
          ),
        },
      ],
    },
    {
      key: 'deployment',
      items: [
        {
          key: 'lineage',
          label: 'Lineage',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyL',
            label: '⌥L',
            path: '/asset-groups',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="lineage" />}
              label="Lineage"
              href="/asset-groups"
              isActive={lineagePathMatcher}
            />
          ),
        },
        {
          key: 'deployment',
          label: 'Deployment',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyD',
            label: '⌥D',
            path: '/deployment',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="settings" />}
              label="Deployment"
              href="/deployment"
              isActive={deploymentPathMatcher}
            />
          ),
        },
      ],
    },
  ];
};

const SupportItem = () => {
  const [isOpen, setIsOpen] = useState(false);
  const {isCollapsed} = useContext(NavCollapseContext);

  return (
    <Popover
      isOpen={isOpen}
      content={<HelpMenuContents dismissDaggyU={() => {}} showContactSales={false} />}
      onClose={() => setIsOpen(false)}
      placement={isCollapsed ? 'right-end' : 'top'}
      matchTargetWidth={!isCollapsed}
    >
      <Tooltip content="Support" placement="right" canShow={isCollapsed}>
        <UnstyledButton
          onClick={() => setIsOpen((current) => !current)}
          className={styles.itemButton}
        >
          <NavItemContent icon={<Icon name="support" />} label="Support" collapsed={isCollapsed} />
        </UnstyledButton>
      </Tooltip>
    </Popover>
  );
};

const CollapseItem = () => {
  const {isCollapsed, toggleCollapsed} = useContext(NavCollapseContext);

  return (
    <ShortcutHandler
      shortcutFilter={(event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyB'}
      shortcutLabel="⌥B"
      onShortcut={toggleCollapsed}
    >
      <Tooltip content="Show navigation" placement="right" canShow={isCollapsed}>
        <UnstyledButton className={styles.itemButton} onClick={() => toggleCollapsed()}>
          <NavItemContent
            icon={<Icon name={isCollapsed ? 'panel_show_left' : 'panel_show_right'} />}
            label="Hide navigation"
            collapsed={isCollapsed}
          />
        </UnstyledButton>
      </Tooltip>
    </ShortcutHandler>
  );
};

const SearchItem = () => {
  const {openSearch, overlay} = useSearchDialog();
  const {isCollapsed} = useContext(NavCollapseContext);

  return (
    <>
      <ShortcutHandler
        shortcutFilter={(event: KeyboardEvent) => {
          return event.code === 'Slash' || (onlyCommandKey(event) && event.code === 'KeyK');
        }}
        shortcutLabel="/ or ⌘K"
        onShortcut={() => openSearch()}
      >
        <Tooltip content="Search" placement="right" canShow={isCollapsed}>
          <UnstyledButton onClick={() => openSearch()} className={styles.itemButton}>
            <NavItemContent icon={<Icon name="search" />} label="Search" collapsed={isCollapsed} />
          </UnstyledButton>
        </Tooltip>
      </ShortcutHandler>
      {overlay}
    </>
  );
};

const SettingsItem = () => {
  const [isOpen, setIsOpen] = useState(false);
  const {isCollapsed} = useContext(NavCollapseContext);
  const visibleFlags = useVisibleFeatureFlagRows();

  return (
    <>
      <ShortcutHandler
        shortcutFilter={(event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyU'}
        shortcutLabel="⌥U"
        onShortcut={() => setIsOpen(true)}
      >
        <Tooltip content="Settings" placement="right" canShow={isCollapsed}>
          <UnstyledButton onClick={() => setIsOpen(true)} className={styles.itemButton}>
            <NavItemContent
              icon={<Icon name="settings" />}
              label="Settings"
              collapsed={isCollapsed}
            />
          </UnstyledButton>
        </Tooltip>
      </ShortcutHandler>
      <UserSettingsDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        visibleFlags={visibleFlags}
      />
    </>
  );
};

export const getBottomGroups = ({featureFlags}: NavigationGroupConfig): NavigationGroup[] => {
  const searchGroup = [
    {
      key: 'search',
      items: [
        {
          key: 'search',
          label: 'Search',
          element: <SearchItem />,
        },
      ],
    },
  ];

  const adminGroup = {
    key: 'support',
    items: [
      {
        key: 'collapse',
        label: 'Collapse',
        element: <CollapseItem />,
      },
      {
        key: 'settings',
        label: 'Settings',
        element: <SettingsItem />,
      },
      {
        key: 'support',
        label: 'Support',
        element: <SupportItem />,
      },
    ],
  };

  if (featureFlags.flagMarketplace) {
    adminGroup.items.unshift({
      key: 'marketplace',
      label: 'Marketplace',
      element: (
        <NavItemWithLink
          icon={<Icon name="compute_kind" />}
          label="Integrations"
          href="/integrations"
          isActive={(_, currentLocation) => currentLocation.pathname.startsWith('/integrations')}
        />
      ),
    });
  }

  return [...searchGroup, adminGroup];
};
