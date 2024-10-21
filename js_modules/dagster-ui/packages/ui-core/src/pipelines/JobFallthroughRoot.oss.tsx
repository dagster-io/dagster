import {PipelineOverviewRoot} from './PipelineOverviewRoot';
import {RepoAddress} from '../workspace/types';

export const JobFallthroughRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  return <PipelineOverviewRoot repoAddress={repoAddress} />;
};
