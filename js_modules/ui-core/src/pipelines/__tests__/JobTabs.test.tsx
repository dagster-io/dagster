import {buildJobTabs} from '../../shared/pipelines/buildJobTabs';

describe('buildJobTabs', () => {
  it('hides the Automation tab for jobs without an automation condition', () => {
    const tabs = buildJobTabs({
      hasLaunchpad: true,
      hasPartitionSet: false,
      hasAutomationCondition: false,
    });
    expect(tabs.map((tab) => tab.id)).toEqual(['overview', 'launchpad', 'runs']);
  });

  it('shows the Automation tab for jobs with an automation condition', () => {
    const tabs = buildJobTabs({
      hasLaunchpad: true,
      hasPartitionSet: false,
      hasAutomationCondition: true,
    });
    expect(tabs.map((tab) => tab.id)).toEqual(['overview', 'launchpad', 'runs', 'automation']);
  });

  it('orders the Automation tab after Partitions', () => {
    const tabs = buildJobTabs({
      hasLaunchpad: true,
      hasPartitionSet: true,
      hasAutomationCondition: true,
    });
    expect(tabs.map((tab) => tab.id)).toEqual([
      'overview',
      'launchpad',
      'runs',
      'partitions',
      'automation',
    ]);
  });
});
