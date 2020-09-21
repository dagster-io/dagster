import {Colors, Icon, IconName} from '@blueprintjs/core';
import React from 'react';
import {Link, LinkProps, useRouteMatch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useRepository} from '../DagsterRepositoryContext';
import {explorerPathFromString, explorerPathToString} from '../PipelinePathUtils';

const PIPELINE_TABS: {
  title: string;
  pathComponent: string;
  icon: IconName;
}[] = [
  {title: 'Overview', pathComponent: 'overview', icon: 'dashboard'},
  {title: 'Definition', pathComponent: '', icon: 'diagram-tree'},
  {
    title: 'Playground',
    pathComponent: 'playground',
    icon: 'manually-entered-data',
  },
  {
    title: 'Runs',
    pathComponent: 'runs',
    icon: 'history',
  },
  {
    title: 'Partitions',
    pathComponent: 'partitions',
    icon: 'multi-select',
  },
];

export function tabForPipelinePathComponent(component?: string) {
  return (
    PIPELINE_TABS.find((t) => t.pathComponent === component) ||
    PIPELINE_TABS.find((t) => t.pathComponent === '')!
  );
}

export const PipelineNav: React.FunctionComponent = () => {
  const repository = useRepository();
  const match = useRouteMatch<{tab: string; selector: string}>(['/pipeline/:selector/:tab?']);
  if (!match) {
    return <span />;
  }

  const active = tabForPipelinePathComponent(match.params.tab);
  const explorerPath = explorerPathFromString(match.params.selector);
  const hasPartitionSet = repository?.partitionSets
    .map((x) => x.pipelineName)
    .includes(explorerPath.pipelineName);

  // When you click one of the top tabs, it resets the snapshot you may be looking at
  // in the Definition tab and also clears solids from the path
  const explorerPathWithoutSnapshot = explorerPathToString({
    ...explorerPath,
    snapshotId: undefined,
    pathSolids: [],
  });

  return (
    <PipelineTabBarContainer>
      <PipelineName>{explorerPath.pipelineName}</PipelineName>
      {PIPELINE_TABS.filter((tab) => hasPartitionSet || tab.pathComponent !== 'partitions').map(
        (tab) => (
          <PipelineTab
            key={tab.title}
            tab={tab}
            active={active === tab}
            to={`/pipeline/${explorerPathWithoutSnapshot}${tab.pathComponent}`}
          />
        ),
      )}
    </PipelineTabBarContainer>
  );
};

const PipelineTabBarContainer = styled.div`
  height: 45px;
  display: flex;
  flex-direction: row;
  flex: 0 0 auto;
  align-items: center;
  border-bottom: 1px solid ${Colors.GRAY5};
  background: ${Colors.LIGHT_GRAY3};
  padding: 2px 10px;
  z-index: 3;
`;

interface PipelineTabProps {
  tab: typeof PIPELINE_TABS[0];
  to: string;
  active?: boolean;
  disabled?: boolean;
}

const PipelineTab = (props: PipelineTabProps) => {
  const {tab, to, active, disabled} = props;
  return (
    <PipelineTabContainer active={!!active} disabled={!!disabled} to={to}>
      <Icon icon={tab.icon} iconSize={16} style={{paddingRight: 8}} />
      {tab.title}
    </PipelineTabContainer>
  );
};

const PipelineName = styled.div`
  font-size: 15px;
  font-weight: 500;
  padding-top: 3px;
  margin-left: 10px;
  margin-right: 30px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
`;

interface TabProps {
  active?: boolean;
  disabled?: boolean;
}

const background = (props: TabProps) => {
  return props.active ? Colors.WHITE : Colors.LIGHT_GRAY1;
};

const color = (props: TabProps) => {
  return props.active ? Colors.BLACK : Colors.DARK_GRAY3;
};

const cursor = (props: TabProps) => {
  const {active, disabled} = props;
  return active || disabled ? 'default' : 'pointer';
};

// Wrapped so that our custom props aren't passed along to the RR `Link`, and
// `disabled` links simply render as divs.
const WrappedLink = (props: TabProps & LinkProps) => {
  const {active, disabled, ...remaining} = props;
  return disabled ? <div /> : <Link {...remaining} />;
};

const PipelineTabContainer = styled(WrappedLink)`
  color: ${color};

  padding: 0 12px 3px 12px;
  display: inline-block;
  border-left: 1px solid ${Colors.GRAY4};
  user-select: none;
  cursor: ${cursor};
  background: ${background};
  border-top: 2px solid ${({active}) => (active ? '#2965CC' : Colors.GRAY5)};
  line-height: 33px;
  height: 40px;
  position: relative;
  white-space: nowrap;
  top: 3px;
  opacity: ${({disabled}) => (disabled ? '0.6' : '1')};

  & .bp3-icon {
    opacity: ${({active}) => (active ? 1 : 0.8)};
  }
  &:hover {
    background: ${background};
    color: ${color};
    cursor: ${cursor};
    text-decoration: none;
  }
`;
