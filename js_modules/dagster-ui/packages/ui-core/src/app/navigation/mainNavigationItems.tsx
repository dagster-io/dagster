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
          label: '概览',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyO',
            label: '⌥O',
            path: '/overview',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="timeline" />}
              label="概览"
              href="/overview"
              isActive={(_, currentLocation) => currentLocation.pathname.startsWith('/overview')}
            />
          ),
        },
        {
          key: 'runs',
          label: '运行记录',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyR',
            label: '⌥R',
            path: '/runs',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="runs" />}
              label="运行记录"
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
          label: '资产目录',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyC',
            label: '⌥C',
            path: '/assets',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="catalog_book" />}
              label="资产目录"
              href="/assets"
              isActive={assetsPathMatcher}
            />
          ),
        },
        jobState === 'has-jobs'
          ? {
              key: 'jobs',
              label: '作业',
              shortcut: {
                filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyJ',
                label: '⌥J',
                path: '/jobs',
              },
              element: (
                <NavItemWithLink
                  icon={<Icon name="column_lineage" />}
                  label="作业"
                  href="/jobs"
                  isActive={jobsPathMatcher}
                />
              ),
            }
          : null,
        {
          key: 'automation',
          label: '自动化',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyA',
            label: '⌥A',
            path: '/automation',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="schedule" />}
              label="自动化"
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
          label: '数据血缘',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyL',
            label: '⌥L',
            path: '/asset-groups',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="lineage" />}
              label="数据血缘"
              href="/asset-groups"
              isActive={lineagePathMatcher}
            />
          ),
        },
        {
          key: 'strategy',
          label: '策略配置',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyS',
            label: '⌥S',
            path: '/strategy',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="tune" />}
              label="策略配置"
              href="/strategy"
              isActive={(_, currentLocation) => currentLocation.pathname.startsWith('/strategy')}
            />
          ),
        },
        {
          key: 'deployment',
          label: '部署',
          shortcut: {
            filter: (event: KeyboardEvent) => onlyAltKey(event) && event.code === 'KeyD',
            label: '⌥D',
            path: '/deployment',
          },
          element: (
            <NavItemWithLink
              icon={<Icon name="settings" />}
              label="部署"
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
      <Tooltip content="帮助" placement="right" canShow={isCollapsed}>
        <UnstyledButton
          onClick={() => setIsOpen((current) => !current)}
          className={styles.itemButton}
        >
          <NavItemContent icon={<Icon name="support" />} label="帮助" collapsed={isCollapsed} />
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
      <Tooltip content="显示导航" placement="right" canShow={isCollapsed}>
        <UnstyledButton className={styles.itemButton} onClick={() => toggleCollapsed()}>
          <NavItemContent
            icon={<Icon name={isCollapsed ? 'panel_show_left' : 'panel_show_right'} />}
            label="隐藏导航"
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
        <Tooltip content="搜索" placement="right" canShow={isCollapsed}>
          <UnstyledButton onClick={() => openSearch()} className={styles.itemButton}>
            <NavItemContent icon={<Icon name="search" />} label="搜索" collapsed={isCollapsed} />
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
        <Tooltip content="设置" placement="right" canShow={isCollapsed}>
          <UnstyledButton onClick={() => setIsOpen(true)} className={styles.itemButton}>
            <NavItemContent
              icon={<Icon name="settings" />}
              label="设置"
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
          label: '搜索',
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
        label: '折叠',
        element: <CollapseItem />,
      },
      {
        key: 'settings',
        label: '设置',
        element: <SettingsItem />,
      },
      {
        key: 'support',
        label: '帮助',
        element: <SupportItem />,
      },
    ],
  };

  if (featureFlags.flagMarketplace) {
    adminGroup.items.unshift({
      key: 'marketplace',
      label: '集成',
      element: (
        <NavItemWithLink
          icon={<Icon name="compute_kind" />}
          label="集成"
          href="/integrations"
          isActive={(_, currentLocation) => currentLocation.pathname.startsWith('/integrations')}
        />
      ),
    });
  }

  return [...searchGroup, adminGroup];
};
