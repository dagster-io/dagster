import {Tabs} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {useLocation} from 'react-router-dom';

import {TabLink} from '../ui/TabLink';

const items = [
  {
    key: 'code-locations',
    label: 'Code locations',
    path: '/deployment/locations',
  },
  {
    key: 'daemons',
    label: 'Daemons',
    path: '/deployment/daemons',
  },
  {
    key: 'concurrency',
    label: 'Concurrency',
    path: '/deployment/concurrency',
  },
  {
    key: 'config',
    label: 'Configuration (read-only)',
    path: '/deployment/config',
  },
];

export const SettingsTabs = () => {
  const {pathname} = useLocation();
  const selectedTabId = useMemo(() => {
    const match = items.find((item) => pathname.startsWith(item.path));
    return match?.key;
  }, [pathname]);

  return (
    <Tabs selectedTabId={selectedTabId}>
      {items.map((item) => (
        <TabLink key={item.key} id={item.key} to={item.path} title={item.label} />
      ))}
    </Tabs>
  );
};
