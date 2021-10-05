import * as React from 'react';
import styled from 'styled-components/macro';

import {ConfigEditorHelpContext} from '../configeditor/ConfigEditorHelpContext';
import {isHelpContextEqual} from '../configeditor/isHelpContextEqual';
import {ConfigTypeSchema, TypeData} from '../typeexplorer/ConfigTypeSchema';
import {ColorsWIP} from '../ui/Colors';

interface ConfigEditorHelpProps {
  context: ConfigEditorHelpContext | null;
  allInnerTypes: TypeData[];
}

export const ConfigEditorHelp: React.FunctionComponent<ConfigEditorHelpProps> = React.memo(
  ({context, allInnerTypes}) => {
    if (!context) {
      return <Container />;
    }
    return (
      <Container>
        <ConfigScrollWrap>
          <ConfigTypeSchema type={context.type} typesInScope={allInnerTypes} maxDepth={2} />
        </ConfigScrollWrap>
        <AutocompletionsNote>Ctrl+Space to show auto-completions inline.</AutocompletionsNote>
      </Container>
    );
  },
  (prev, next) => isHelpContextEqual(prev.context, next.context),
);

const AutocompletionsNote = styled.div`
  font-size: 0.75rem;
  text-align: center;
  padding: 4px;
  border-top: 1px solid ${ColorsWIP.Gray200};
  background: rgba(238, 238, 238, 0.9);
  color: rgba(0, 0, 0, 0.7);
`;

const ConfigScrollWrap = styled.div`
  padding: 8px;
  color: black;
  flex: 1;
  pointer-events: initial;
  max-height: 100%;
  overflow-y: auto;
`;

const Container = styled.div`
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: #e1e8edd1;
  height: 100%;
`;
