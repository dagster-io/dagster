import {Box, Button, Colors, Icon, Table, Tooltip} from '@dagster-io/ui-components';
import {useState} from 'react';
import * as React from 'react';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {RunConfigDialog} from '../runs/RunConfigDialog';
import {assetKeysForRun} from '../runs/RunUtils';
import {RunRequestFragment} from './types/RunRequestFragment.types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {AssetCheckTagCollection, AssetKeyTagCollection} from '../runs/AssetTagCollections';
import {testId} from '../testing/testId';
import {useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';

type RequestProps = {
  name: string;
  jobName: string;
  runRequest: RunRequestFragment;
  repoAddress: RepoAddress;
  isJob: boolean;
};

export const RequestReference = ({name, jobName, runRequest, repoAddress, isJob}: RequestProps) => {
  const repo = useRepository(repoAddress);
  const finalJobName = runRequest.jobName ?? jobName;
  const assetKeys = React.useMemo(() => {
    return isHiddenAssetGroupJob(finalJobName)
      ? assetKeysForRun({assetSelection: runRequest.assetSelection, stepKeysToExecute: null})
      : null;
  }, [runRequest.assetSelection, finalJobName]);

  if (isHiddenAssetGroupJob(finalJobName)) {
    // If the asset selection is null, it means that the run will materialize all assets targeted by
    // the scheedule/sensor. If the asset selection is the empty list, the run will not target any assets
    const assetSelectionItems =
      runRequest.assetSelection !== null && runRequest.assetSelection !== undefined ? (
        runRequest.assetSelection.length > 0 ? (
          <AssetKeyTagCollection
            assetKeys={runRequest.assetSelection}
            useTags
            maxRows={runRequest.assetChecks?.length ? 1 : 2}
          />
        ) : (
          <span>No assets</span>
        )
      ) : (
        <span>All assets targeted by {name}</span>
      );

    // If the asset check selection is null, it means that the run will materialize all asset checks targeted by
    // the scheedule/sensor. If the asset check selection is the empty list, the run will not target any assets checks
    const assetCheckItems =
      runRequest.assetChecks !== null && runRequest.assetChecks !== undefined ? (
        runRequest.assetChecks.length > 0 ? (
          <AssetCheckTagCollection
            assetChecks={runRequest.assetChecks}
            maxRows={runRequest.assetSelection?.length ? 1 : 2}
          />
        ) : (
          <span>No asset checks</span>
        )
      ) : (
        <span>All asset checks targeted by {name}</span>
      );

    return (
      <Box flex={{direction: 'column', gap: 4}}>
        {assetSelectionItems}
        {assetCheckItems}
      </Box>
    );
  }

  if (assetKeys) {
    return (
      <Box flex={{direction: 'column', gap: 4}}>
        <AssetKeyTagCollection
          assetKeys={assetKeys}
          useTags
          maxRows={runRequest.assetChecks?.length ? 1 : 2}
        />
        <AssetCheckTagCollection
          assetChecks={runRequest.assetChecks}
          maxRows={assetKeys?.length ? 1 : 2}
        />
      </Box>
    );
  }
  return (
    <PipelineReference
      pipelineName={finalJobName}
      pipelineHrefContext={repoAddress}
      isJob={!!repo && isJob}
    />
  );
};

type Props = {
  name: string;
  runRequests: RunRequestFragment[];
  repoAddress: RepoAddress;
  isJob: boolean;
  jobName: string;
  mode?: string;
};

export const RunRequestTable = ({name, runRequests, isJob, repoAddress, mode, jobName}: Props) => {
  const [selectedRequest, setSelectedRequest] = useState<RunRequestFragment | null>(null);
  const [visibleDialog, setVisibleDialog] = useState<'config' | null>(null);

  const body = (
    <tbody data-testid={testId('table-body')}>
      {runRequests.map((request, index) => {
        return (
          <tr key={index} data-testid={testId(request.runKey || '')}>
            <td style={{verticalAlign: 'middle'}}>
              <Box flex={{alignItems: 'center', gap: 8}}>
                <RequestReference
                  name={name}
                  jobName={request.jobName ?? jobName}
                  repoAddress={repoAddress}
                  isJob={isJob}
                  runRequest={request}
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
