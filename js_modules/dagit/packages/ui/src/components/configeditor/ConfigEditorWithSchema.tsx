import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {Box} from '../Box';
import {Spinner} from '../Spinner';
import {SplitPanelContainer} from '../SplitPanelContainer';

import type {ConfigSchema} from './ConfigEditor';
import {ConfigEditor} from './ConfigEditor';
import {ConfigEditorHelp} from './ConfigEditorHelp';
import {ConfigEditorHelpContext} from './ConfigEditorHelpContext';
import {isHelpContextEqual} from './isHelpContextEqual';

interface Props {
  onConfigChange: (config: string) => void;
  config: string | undefined;
  configSchema: ConfigSchema;
  isLoading: boolean;
  identifier: string;
}

// Force code editor hints to appear above the dialog modal
const CodeMirrorShimStyle = createGlobalStyle`
  .CodeMirror-hints {
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
              allInnerTypes={(configSchema?.allConfigTypes as any) || []}
            />
          </Box>
        }
      />
    </>
  );
};
