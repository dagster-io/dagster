import * as React from 'react';

import {RepoAddress} from '../workspace/types';

import {JobTabConfig, JobTabConfigInput, buildJobTabs} from './JobTabs';
import {PipelineOverviewRoot} from './PipelineOverviewRoot';

export type JobViewFeatureInput = {
  selectedTab: string;
};

export interface JobRouteFallthroughProps {
  repoAddress: RepoAddress;
}

type JobFeatureContextType = {
  tabBuilder: (input: JobTabConfigInput) => JobTabConfig[];
  FallthroughRoute: (props: JobRouteFallthroughProps) => React.ReactElement;
};

export const JobFeatureContext = React.createContext<JobFeatureContextType>({
  tabBuilder: () => [],
  FallthroughRoute: () => <span />,
});

const FallthroughRoute = ({repoAddress}: JobRouteFallthroughProps) => {
  return <PipelineOverviewRoot repoAddress={repoAddress} />;
};

export const JobFeatureProvider = ({children}: {children: React.ReactNode}) => {
  const value = React.useMemo(() => {
    return {
      tabBuilder: buildJobTabs,
      FallthroughRoute,
    };
  }, []);

  return <JobFeatureContext.Provider value={value}>{children}</JobFeatureContext.Provider>;
};
