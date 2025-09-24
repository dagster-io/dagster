import {useRef, useState} from 'react';
import {createGlobalStyle} from 'styled-components';

import {Box} from './Box';
import {ConfigEditorHandle, ConfigSchema, NewConfigEditor} from './NewConfigEditor';
import {Spinner} from './Spinner';
import {SplitPanelContainer, SplitPanelContainerHandle} from './SplitPanelContainer';
import {ConfigEditorHelp} from './configeditor/ConfigEditorHelp';
import {isHelpContextEqual} from './configeditor/isHelpContextEqual';
import {ConfigEditorHelpContext} from './configeditor/types/ConfigEditorHelpContext';

interface Props {
  onConfigChange: (config: string) => void;
  config?: string;
  configSchema?: ConfigSchema | null;
  isLoading: boolean;
  identifier: string;
}

// Force code editor hints to appear above the dialog modal
export const CodeMirrorInDialogStyle = createGlobalStyle`
  .CodeMirror-hints,
  .CodeMirror-hints.dagster {
    z-index: 100;
  }
`;

export const ConfigEditorWithSchema = ({
  isLoading,
  identifier,
  config,
  onConfigChange,
  configSchema,
}: Props) => {
  const editorSplitPanelContainer = useRef<SplitPanelContainerHandle | null>(null);
  const [editorHelpContext, setEditorHelpContext] = useState<ConfigEditorHelpContext | null>(null);
  const editor = useRef<ConfigEditorHandle | null>(null);

  return (
    <>
      <CodeMirrorInDialogStyle />
      <SplitPanelContainer
        ref={editorSplitPanelContainer}
        axis="horizontal"
        identifier={identifier}
        firstMinSize={100}
        firstInitialPercent={70}
        first={
          !isLoading ? (
            <NewConfigEditor
              ref={editor}
              configCode={config ?? ''}
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
              configSchema={configSchema}
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
    </>
  );
};
