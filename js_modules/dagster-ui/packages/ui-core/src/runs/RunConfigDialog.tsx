import {
  Box,
  Button,
  Dialog,
  DialogFooter,
  StyledRawCodeMirror,
  Subheading,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {RunTags} from './RunTags';
import {RunTagsFragment} from './types/RunTable.types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  copyConfig: () => void;
  runConfigYaml: string;
  mode: string | null;
  isJob: boolean;

  // Optionally provide tags to display them as well.
  tags?: RunTagsFragment[];
}

export const RunConfigDialog = (props: Props) => {
  const {isOpen, onClose, copyConfig, runConfigYaml, tags, mode, isJob} = props;
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
        <DialogFooter topBorder>
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

const CodeMirrorContainer = styled.div`
  flex: 1;
  overflow: hidden;

  .CodeMirror {
    height: 100%;
  }
`;
