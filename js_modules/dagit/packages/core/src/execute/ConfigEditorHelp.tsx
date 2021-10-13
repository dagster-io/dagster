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
        <AutocompletionsNote>Use Ctrl+Space to show auto-completions inline.</AutocompletionsNote>
      </Container>
    );
  },
  (prev, next) => isHelpContextEqual(prev.context, next.context),
);

const AutocompletionsNote = styled.div`
  font-size: 0.75rem;
  text-align: center;
  padding: 4px;
  border-top: 1px solid ${ColorsWIP.KeylineGray};
  background: ${ColorsWIP.Gray100};
  color: ${ColorsWIP.Gray500};
`;

const ConfigScrollWrap = styled.div`
  padding: 8px;
  color: ${ColorsWIP.Dark};
  flex: 1;
  pointer-events: initial;
  max-height: 100%;
  overflow-y: auto;
`;

const Container = styled.div`
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: ${ColorsWIP.Gray50};
  height: 100%;
`;
