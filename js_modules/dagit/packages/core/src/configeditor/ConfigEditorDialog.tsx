import {
  Box,
  Button,
  DialogFooter,
  Dialog,
  SplitPanelContainer,
  Spinner,
  Tooltip,
  Icon,
} from '@dagster-io/ui';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {ConfigEditorHelp} from '../launchpad/ConfigEditorHelp';

import {ConfigEditor} from './ConfigEditor';
import {ConfigEditorHelpContext} from './ConfigEditorHelpContext';
import {isHelpContextEqual} from './isHelpContextEqual';

interface Props {
  onConfigChange: (config: string) => void;
  onSave: () => void;
  onClose: () => void;
  config: string | undefined;
  configSchema: any | undefined;
  isLoading: boolean;
  saveText: string;
  identifier: string;
  title: string;
  isSubmitting: boolean;
  error?: string | null;
  isOpen: boolean;
}

// Force code editor hints to appear above the dialog modal
const CodeMirrorShimStyle = createGlobalStyle`
  .CodeMirror-hints {
    z-index: 100;
  }
`;

export const YAMLEditorDialog: React.FC<Props> = ({
  config,
  configSchema,
  isLoading,
  isSubmitting,
  error,
  onSave,
  onClose,
  onConfigChange,
  identifier,
  title,
  saveText,
  isOpen,
}) => {
  const editorSplitPanelContainer = React.useRef<SplitPanelContainer | null>(null);
  const [editorHelpContext, setEditorHelpContext] = React.useState<ConfigEditorHelpContext | null>(
    null,
  );
  const editor = React.useRef<ConfigEditor | null>(null);

  return (
    <Dialog
      isOpen={isOpen}
      title={title}
      onClose={onClose}
      style={{maxWidth: '90%', minWidth: '70%', width: 1000}}
    >
      <CodeMirrorShimStyle />
      <SplitPanelContainer
        ref={editorSplitPanelContainer}
        axis="horizontal"
        identifier={identifier}
        firstMinSize={100}
        firstInitialPercent={70}
        first={
          !isLoading ? (
            <ConfigEditor
              ref={editor}
              configCode={config!}
              onConfigChange={onConfigChange}
              onHelpContextChange={(next) => {
                if (next && !isHelpContextEqual(editorHelpContext, next)) {
                  setEditorHelpContext(next);
                }
              }}
              readOnly={false}
              checkConfig={async (_j) => {
                return {isValid: true};
              }}
              runConfigSchema={configSchema}
            />
          ) : (
            <Box style={{height: '100%'}} flex={{alignItems: 'center', justifyContent: 'center'}}>
              <Spinner purpose="section" />
            </Box>
          )
        }
        second={
          <Box style={{height: 500}}>
            <ConfigEditorHelp
              context={editorHelpContext}
              allInnerTypes={configSchema?.allConfigTypes || []}
            />
          </Box>
        }
      />
      <DialogFooter topBorder>
        {error ? (
          <Tooltip
            isOpen={true}
            content={error}
            placement="bottom-start"
            modifiers={{offset: {enabled: true, options: {offset: [0, 16]}}}}
          >
            <Icon name="warning" />
          </Tooltip>
        ) : null}
        <Button intent="primary" onClick={onSave} disabled={isLoading || !!error || isSubmitting}>
          {saveText}
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
