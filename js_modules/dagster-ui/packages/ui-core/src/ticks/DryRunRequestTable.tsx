import {Box, Button, Colors, Icon, Table, Tag} from '@dagster-io/ui-components';

import {applyCreateSession, useExecutionSessionStorage} from '../app/ExecutionSessionStorage';
import {RunRequestFragment} from './types/RunRequestFragment.types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {testId} from '../testing/testId';
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
              <OpenInLaunchpadButton
                request={request}
                mode={mode}
                jobName={jobName}
                repoAddress={repoAddress}
                isJob={isJob}
              />
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

function OpenInLaunchpadButton({
  mode,
  request,
  jobName,
  isJob,
  repoAddress,
}: {
  request: RunRequestFragment;
  jobName?: string;
  mode?: string;
  repoAddress: RepoAddress;
  isJob: boolean;
}) {
  const pipelineName = request.jobName ?? jobName;
  const [_, onSave] = useExecutionSessionStorage(repoAddress, pipelineName!);

  return (
    <Button
      icon={<Icon name="edit" />}
      onClick={() => {
        onSave((data) =>
          applyCreateSession(data, {
            mode,
            runConfigYaml: request.runConfigYaml,
            tags: request.tags,
            assetSelection: request.assetSelection?.map(({path}) => ({
              assetKey: {path},
            })),
          }),
        );
        window.open(
          workspacePathFromAddress(
            repoAddress,
            `/${isJob ? 'jobs' : 'pipelines'}/${pipelineName}/playground`,
          ),
          '_blank',
        );
      }}
    >
      Open in Launchpad
    </Button>
  );
}
