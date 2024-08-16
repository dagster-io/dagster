import {Box, Icon} from '@dagster-io/ui-components';
import {useState} from 'react';
import {useLocation} from 'react-router-dom';
import {useVisibleFeatureFlagRows} from 'shared/app/useVisibleFeatureFlagRows.oss';

import {UserSettingsDialog} from '../app/UserSettingsDialog/UserSettingsDialog';
import {SideNavItem, SideNavItemConfig} from '../ui/SideNavItem';

const items: SideNavItemConfig[] = [
  {
    key: 'code-locations',
    type: 'link',
    icon: <Icon name="code_location" />,
    label: 'Code locations',
    path: '/deployment/locations',
  },
  {
    key: 'daemons',
    type: 'link',
    icon: <Icon name="daemon" />,
    label: 'Daemons',
    path: '/deployment/daemons',
  },
  {
    key: 'concurrency-limits',
    type: 'link',
    icon: <Icon name="concurrency" />,
    label: 'Concurrency limits',
    path: '/deployment/concurrency',
  },
  {
    key: 'config',
    type: 'link',
    icon: <Icon name="tune" />,
    label: 'Configuration (read-only)',
    path: '/deployment/config',
  },
];

export const SettingsLeftPane = () => {
  const {pathname} = useLocation();
  const [showUserSettings, setShowUserSettings] = useState(false);

  const userSettingsItem: SideNavItemConfig = {
    key: 'user-settings',
    type: 'button',
    icon: <Icon name="account_circle" />,
    label: 'User settings',
    onClick: () => setShowUserSettings(true),
  };

  return (
    <Box padding={12}>
      <Box padding={{bottom: 12}}>
        {items.map((item) => {
          return (
            <SideNavItem
              key={item.key}
              item={item}
              active={item.type === 'link' && pathname === item.path}
            />
          );
        })}
      </Box>
      <Box padding={{top: 16}} border="top">
        <>
          <SideNavItem item={userSettingsItem} />
          <UserSettingsDialog
            isOpen={showUserSettings}
            onClose={() => setShowUserSettings(false)}
            visibleFlags={useVisibleFeatureFlagRows()}
          />
        </>
      </Box>
    </Box>
  );
};
