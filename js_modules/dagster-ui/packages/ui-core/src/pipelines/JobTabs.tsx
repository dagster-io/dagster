import * as React from 'react';

import {Tab, Tabs, Tooltip} from '@dagster-io/ui-components';

import {PermissionResult, PermissionsState, permissionResultForKey} from '../app/Permissions';
import {TabLink} from '../ui/TabLink';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';
import {ExplorerPath, explorerPathToString} from './PipelinePathUtils';

export const DEFAULT_JOB_TAB_ORDER = ['overview', 'playground', 'runs', 'partitions'];

interface Props {
  repoAddress: RepoAddress;
  isJob: boolean;
  explorerPath: ExplorerPath;
  matchingTab?: string;
  permissions: PermissionsState;
  tabs: JobTabConfig[];
}

export const JobTabs = (props: Props) => {
  const {repoAddress, isJob, explorerPath, matchingTab = '', permissions, tabs} = props;

  const explorerPathForTab = explorerPathToString({
    ...explorerPath,
    opNames: [],
  });

  const selectedTab = React.useMemo(() => {
    return (
      tabs.find((tab) => tab.pathComponent === matchingTab) ||
      tabs.find((tab) => tab.pathComponent === '')
    );
  }, [matchingTab, tabs]);

  return (
    <Tabs size="large" selectedTabId={selectedTab!.id}>
      {tabs
        .filter((tab) => !tab.isHidden)
        .map((tab) => {
          const {id, title: text, getPermissionsResult} = tab;
          const permissionsResult = getPermissionsResult ? getPermissionsResult(permissions) : null;
          const disabled = !!(permissionsResult && !permissionsResult.enabled);
          const title =
            permissionsResult && disabled ? (
              <Tooltip content={permissionsResult.disabledReason} placement="top">
                {text}
              </Tooltip>
            ) : (
              text
            );

          const href = workspacePathFromAddress(
            repoAddress,
            `/${isJob ? 'jobs' : 'pipelines'}/${explorerPathForTab}${tab.pathComponent}`,
          );

          if (disabled) {
            return <Tab disabled key={id} id={id} title={title} />;
          }

          return <TabLink key={id} id={id} title={title} disabled={disabled} to={href} />;
        })}
    </Tabs>
  );
};

export type JobTabConfigInput = {
  hasLaunchpad: boolean;
  hasPartitionSet: boolean;
};

export interface JobTabConfig {
  id: string;
  title: string;
  pathComponent: string;
  getPermissionsResult?: (permissionsState: PermissionsState) => PermissionResult;
  isHidden?: boolean;
}

/**
 * Define the default set of job tabs. These can then be ordered by the `tabBuilder` supplied
 * via context. We provide a map here instead of an array so that the overriding context can easily
 * define a new tab order without splicing or reordering a prebuilt array.
 */
export const buildJobTabMap = (input: JobTabConfigInput): Record<string, JobTabConfig> => {
  const {hasLaunchpad, hasPartitionSet} = input;
  return {
    overview: {
      id: 'overview',
      title: 'Overview',
      pathComponent: '',
    },
    playground: {
      id: 'launchpad',
      title: 'Launchpad',
      pathComponent: 'playground',
      getPermissionsResult: (permissionsState: PermissionsState) =>
        permissionResultForKey(permissionsState, 'canLaunchPipelineExecution'),
      isHidden: !hasLaunchpad,
    },
    runs: {
      id: 'runs',
      title: 'Runs',
      pathComponent: 'runs',
    },
    partitions: {
      id: 'partitions',
      title: 'Partitions',
      pathComponent: 'partitions',
      isHidden: !hasPartitionSet,
    },
  };
};

export const buildJobTabs = (input: JobTabConfigInput): JobTabConfig[] => {
  const tabConfigs = buildJobTabMap(input);
  return DEFAULT_JOB_TAB_ORDER.map((tabId) => tabConfigs[tabId]).filter(
    (tab): tab is JobTabConfig => !!tab && !tab.isHidden,
  );
};
