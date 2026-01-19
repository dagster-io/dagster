import {Tabs} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {useLocation} from 'react-router-dom';

import {TabLink} from '../ui/TabLink';

const items = [
  {
    key: 'code-locations',
    label: '代码位置',
    path: '/deployment/locations',
  },
  {
    key: 'daemons',
    label: '守护进程',
    path: '/deployment/daemons',
  },
  {
    key: 'concurrency',
    label: '并发',
    path: '/deployment/concurrency',
  },
  {
    key: 'config',
    label: '配置 (只读)',
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
