import {DEFAULT_JOB_TAB_ORDER, JobTabConfig, JobTabConfigInput, buildJobTabMap} from './JobTabs';

export const buildJobTabs = (input: JobTabConfigInput): JobTabConfig[] => {
  const tabConfigs = buildJobTabMap(input);
  return DEFAULT_JOB_TAB_ORDER.map((tabId) => tabConfigs[tabId]).filter(
    (tab): tab is JobTabConfig => !!tab && !tab.isHidden,
  );
};
