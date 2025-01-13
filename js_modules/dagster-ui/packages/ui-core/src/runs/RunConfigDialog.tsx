import {Box, Button, Dialog, DialogFooter, Icon, Subheading} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import styled from 'styled-components';

import {RunTags} from './RunTags';
import {RunTagsFragment} from './types/RunTagsFragment.types';
import {applyCreateSession, useExecutionSessionStorage} from '../app/ExecutionSessionStorage';
import {useOpenInNewTab} from '../hooks/useOpenInNewTab';
import {RunRequestFragment} from '../ticks/types/RunRequestFragment.types';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  copyConfig: () => void;
  runConfigYaml: string;
  mode: string | null;
  isJob: boolean;
  jobName?: string;
  // Optionally provide tags to display them as well.
  tags?: RunTagsFragment[];

  // Optionally provide a request to display the "Open in Launchpad" button.
  request?: RunRequestFragment;
  repoAddress?: RepoAddress;
}

export const RunConfigDialog = (props: Props) => {
  const {
    isOpen,
    onClose,
    copyConfig,
    runConfigYaml,
    tags,
    mode,
    isJob,
    jobName,
    request,
    repoAddress,
  } = props;
  const hasTags = !!tags && tags.length > 0;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      canOutsideClickClose
      canEscapeKeyClose
      style={{
        width: '90vw',
        maxWidth: '1000px',
        minWidth: '600px',
        height: '90vh',
        maxHeight: '1000px',
        minHeight: '600px',
      }}
      title="Run configuration"
    >
      <Box flex={{direction: 'column'}} style={{flex: 1, overflow: 'hidden'}}>
        <Box flex={{direction: 'column', gap: 20}} style={{flex: 1, overflow: 'hidden'}}>
          {hasTags ? (
            <Box flex={{direction: 'column', gap: 12}} padding={{top: 16, horizontal: 24}}>
              <Subheading>Tags</Subheading>
              <div>
                <RunTags tags={tags} mode={isJob ? null : mode} />
              </div>
            </Box>
          ) : null}
          <Box flex={{direction: 'column'}} style={{flex: 1, overflow: 'hidden'}}>
            {hasTags ? (
              <Box border="bottom" padding={{left: 24, bottom: 16}}>
                <Subheading>Config</Subheading>
              </Box>
            ) : null}
            <CodeMirrorContainer>
              <StyledRawCodeMirror
                value={runConfigYaml}
                options={{readOnly: true, lineNumbers: true, mode: 'yaml'}}
                theme={['config-editor']}
              />
            </CodeMirrorContainer>
          </Box>
        </Box>
        <DialogFooter
          topBorder
          left={
            request &&
            repoAddress &&
            jobName && (
              <OpenInLaunchpadButton
                request={request}
                mode={mode || null}
                jobName={jobName}
                isJob={isJob}
                repoAddress={repoAddress}
              />
            )
          }
        >
          <Button onClick={() => copyConfig()} intent="none">
            Copy config
          </Button>
          <Button onClick={onClose} intent="primary">
            OK
          </Button>
        </DialogFooter>
      </Box>
    </Dialog>
  );
};

function OpenInLaunchpadButton({
  mode,
  request,
  jobName,
  isJob,
  repoAddress,
}: {
  request: RunRequestFragment;
  jobName?: string;
  mode?: string | null;
  repoAddress: RepoAddress;
  isJob: boolean;
}) {
  const openInNewTab = useOpenInNewTab();
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

        openInNewTab(
          workspacePathFromAddress(
            repoAddress,
            `/${isJob ? 'jobs' : 'pipelines'}/${pipelineName}/playground`,
          ),
        );
      }}
    >
      Open in Launchpad
    </Button>
  );
}

const CodeMirrorContainer = styled.div`
  flex: 1;
  overflow: hidden;

  .CodeMirror {
    height: 100%;
  }
`;
