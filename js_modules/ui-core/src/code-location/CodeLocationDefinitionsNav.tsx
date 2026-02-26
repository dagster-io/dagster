import {Box, Icon, Tag} from '@dagster-io/ui-components';
import {useLocation} from 'react-router-dom';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {SideNavItem, SideNavItemConfig} from '../ui/SideNavItem';
import {numberFormatter} from '../ui/formatters';
import {WorkspaceRepositoryFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  repoAddress: RepoAddress;
  repository: WorkspaceRepositoryFragment;
}

export const CodeLocationDefinitionsNav = (props: Props) => {
  const {repoAddress, repository} = props;
  const {pathname} = useLocation();
  const assetGroupCount = repository.assetGroups.length;
  const jobCount = repository.pipelines.filter(({name}) => !isHiddenAssetGroupJob(name)).length;
  const scheduleCount = repository.schedules.length;
  const sensorCount = repository.sensors.length;
  const resourceCount = repository.allTopLevelResourceDetails.length;

  const items: SideNavItemConfig[] = [
    {
      key: 'assets',
      type: 'link',
      icon: <Icon name="asset" />,
      label: 'Assets',
      path: workspacePathFromAddress(repoAddress, '/assets'),
      rightElement: assetGroupCount ? (
        <Tag icon="asset_group">{numberFormatter.format(assetGroupCount)}</Tag>
      ) : null,
    },
    {
      key: 'jobs',
      type: 'link',
      icon: <Icon name="job" />,
      label: 'Jobs',
      path: workspacePathFromAddress(repoAddress, '/jobs'),
      rightElement: jobCount ? <Tag>{numberFormatter.format(jobCount)}</Tag> : null,
    },
    {
      key: 'sensors',
      type: 'link',
      icon: <Icon name="sensors" />,
      label: 'Sensors',
      path: workspacePathFromAddress(repoAddress, '/sensors'),
      rightElement: sensorCount ? <Tag>{numberFormatter.format(sensorCount)}</Tag> : null,
    },
    {
      key: 'schedules',
      type: 'link',
      icon: <Icon name="schedule" />,
      label: 'Schedules',
      path: workspacePathFromAddress(repoAddress, '/schedules'),
      rightElement: scheduleCount ? <Tag>{numberFormatter.format(scheduleCount)}</Tag> : null,
    },
    {
      key: 'resources',
      type: 'link',
      icon: <Icon name="resource" />,
      label: 'Resources',
      path: workspacePathFromAddress(repoAddress, '/resources'),
      rightElement: resourceCount ? <Tag>{numberFormatter.format(resourceCount)}</Tag> : null,
    },
    {
      key: 'graphs',
      type: 'link',
      icon: <Icon name="graph" />,
      label: 'Graphs',
      path: workspacePathFromAddress(repoAddress, '/graphs'),
    },
    {
      key: 'ops',
      type: 'link',
      icon: <Icon name="op" />,
      label: 'Ops',
      path: workspacePathFromAddress(repoAddress, '/ops'),
    },
  ];

  return (
    <>
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
    </>
  );
};
