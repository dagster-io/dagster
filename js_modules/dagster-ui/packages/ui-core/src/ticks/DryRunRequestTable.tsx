import {Box, Button, Colors, Icon, Table, Tooltip} from '@dagster-io/ui-components';
import {useState} from 'react';

import {RunConfigDialog} from '../runs/RunConfigDialog';
import {RunRequestFragment} from './types/RunRequestFragment.types';
import {showSharedToaster} from '../app/DomUtils';
import {useCopyToClipboard} from '../app/browser';
import {PipelineReference} from '../pipelines/PipelineReference';
import {testId} from '../testing/testId';
import {useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';

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
  const [selectedRequest, setSelectedRequest] = useState<RunRequestFragment | null>(null);
  const [visibleDialog, setVisibleDialog] = useState<'config' | null>(null);
  const copy = useCopyToClipboard();

  const copyConfig = async () => {
    copy(selectedRequest?.runConfigYaml || '');
    await showSharedToaster({
      intent: 'success',
      icon: 'copy_to_clipboard_done',
      message: 'Copied!',
    });
  };

  const body = (
    <tbody data-testid={testId('table-body')}>
      {runRequests.map((request, index) => {
        return (
          <tr key={index} data-testid={testId(request.runKey || '')}>
            <td style={{verticalAlign: 'middle'}}>
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
            <td style={{width: '7.5%', verticalAlign: 'middle', textAlign: 'center'}}>
              <PreviewButton
                request={request}
                onClick={() => {
                  setSelectedRequest(request);
                  setVisibleDialog('config');
                }}
              />
            </td>
          </tr>
        );
      })}
      {selectedRequest && (
        <RunConfigDialog
          isOpen={visibleDialog === 'config'}
          onClose={() => setVisibleDialog(null)}
          copyConfig={() => copyConfig()}
          mode={mode || null}
          runConfigYaml={selectedRequest.runConfigYaml}
          tags={selectedRequest.tags}
          isJob={isJob}
          jobName={jobName}
          request={selectedRequest}
          repoAddress={repoAddress}
        />
      )}
    </tbody>
  );
  return (
    <div>
      <Table style={{borderRight: `1px solid ${Colors.keylineDefault()}`, tableLayout: 'fixed'}}>
        <thead>
          <tr>
            <th>Target</th>
            <th style={{width: '7.5%'}}>Actions</th>
          </tr>
        </thead>
        {body}
      </Table>
    </div>
  );
};

function PreviewButton({request, onClick}: {request: RunRequestFragment; onClick: () => void}) {
  return (
    <Tooltip content="Preview run config and tags" placement="left-start">
      <Button
        icon={<Icon name="data_object" />}
        onClick={onClick}
        data-testid={testId(`preview-${request.runKey || ''}`)}
      />
    </Tooltip>
  );
}
