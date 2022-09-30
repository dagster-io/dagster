import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {Box} from './Box';
import {ConfigEditor, ConfigSchema} from './ConfigEditor';
import {Spinner} from './Spinner';
import {SplitPanelContainer} from './SplitPanelContainer';
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
  .CodeMirror-hints.dagit {
    z-index: 100;
  }
`;

export const ConfigEditorWithSchema: React.FC<Props> = ({
  isLoading,
  identifier,
  config,
  onConfigChange,
  configSchema,
}) => {
  const editorSplitPanelContainer = React.useRef<SplitPanelContainer | null>(null);
  const [editorHelpContext, setEditorHelpContext] = React.useState<ConfigEditorHelpContext | null>(
    null,
  );
  const editor = React.useRef<ConfigEditor | null>(null);

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
