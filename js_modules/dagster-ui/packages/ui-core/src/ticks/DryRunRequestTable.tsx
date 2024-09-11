import {Box, Colors, Icon, Table, Tag} from '@dagster-io/ui-components';
import qs from 'qs';

import {RunRequestFragment} from './types/RunRequestFragment.types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {testId} from '../testing/testId';
import {AnchorButton} from '../ui/AnchorButton';
import {useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

type Props = {
  name: string;
  runRequests: RunRequestFragment[];
  repoAddress: RepoAddress;
  isJob: boolean;
  jobName: string;
  mode?: string;
};

export const RunRequestTable = ({runRequests, isJob, repoAddress, mode, jobName}: Props) => {
  const repo = useRepository(repoAddress);

  const body = (
    <tbody data-testid={testId('table-body')}>
      {runRequests.map((request, index) => {
        return (
          <tr key={index} data-testid={testId(request.runKey || '')}>
            <td>
              <Box flex={{alignItems: 'center', gap: 8}}>
                <PipelineReference
                  pipelineName={request.jobName ?? jobName}
                  pipelineHrefContext={repoAddress}
                  isJob={!!repo && isJob}
                  showIcon
                  size="small"
                />
              </Box>
            </td>
            <td>
              <Box flex={{direction: 'row', gap: 8, wrap: 'wrap'}}>
                {filterTags(request.tags).map(({key, value}) => (
                  <Tag key={key}>{`${key}: ${value}`}</Tag>
                ))}
              </Box>
            </td>
            <td>
              <AnchorButton
                icon={<Icon name="edit" />}
                target="_blank"
                to={workspacePathFromAddress(
                  repoAddress,
                  `/pipeline_or_job/${request.jobName ?? jobName}/playground/setup?${qs.stringify({
                    mode,
                    config: request.runConfigYaml,
                    tags: request.tags,
                    assetSelection: request.assetSelection?.map(({path}) => ({
                      assetKey: {path},
                    })),
                  })}`,
                )}
              >
                Open in Launchpad
              </AnchorButton>
            </td>
          </tr>
        );
      })}
    </tbody>
  );
  return (
    <div>
      <Table style={{borderRight: `1px solid ${Colors.keylineDefault()}`, tableLayout: 'fixed'}}>
        <thead>
          <tr>
            <th>{isJob ? 'Job' : 'Pipeline'} name</th>
            <th>Tags</th>
            <th>Configuration</th>
          </tr>
        </thead>
        {body}
      </Table>
    </div>
  );
};

// Filter out tags we already display in other ways
function filterTags(tags: Array<{key: string; value: any}>) {
  return tags.filter(({key}) => {
    // Exclude the tag that specifies the schedule if this is a schedule name
    return !['dagster/schedule_name'].includes(key);
  });
}
