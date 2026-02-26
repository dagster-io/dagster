import {Box} from '@dagster-io/ui-components';

import {MainNavigationItem} from './MainNavigationItem';
import styles from './css/MainNavigation.module.css';
import {NavigationGroup, NavigationItem} from './types';

interface Props {
  list: NavigationGroup[];
  className?: string;
  collapsed: boolean;
}

export const NavigationGroupDisplay = (props: Props) => {
  const {list, className, collapsed} = props;
  const count = list.length;
  return (
    <Box flex={{direction: 'column'}} className={className}>
      {list.map((group, ii) => (
        <Box
          key={group.key}
          flex={{direction: 'column', gap: 2}}
          border={ii < count - 1 ? 'bottom' : undefined}
          padding={{vertical: 4}}
          className={styles.group}
        >
          {group.items
            .filter((item): item is NavigationItem => !!item)
            .map((item) => (
              <MainNavigationItem key={item.key} item={item} collapsed={collapsed} />
            ))}
        </Box>
      ))}
    </Box>
  );
};
