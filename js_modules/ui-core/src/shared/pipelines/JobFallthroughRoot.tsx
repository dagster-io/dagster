import {PipelineOverviewRoot} from '../../pipelines/PipelineOverviewRoot';
import {RepoAddress} from '../../workspace/types';

export const JobFallthroughRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  return <PipelineOverviewRoot repoAddress={repoAddress} />;
};
