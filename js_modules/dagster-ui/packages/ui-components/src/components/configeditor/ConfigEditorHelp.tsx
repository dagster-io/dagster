import {memo} from 'react';
import styled from 'styled-components';

import {ConfigEditorHelpContext} from './types/ConfigEditorHelpContext';
import {Colors} from '../Color';
import {ConfigTypeSchema, TypeData} from '../ConfigTypeSchema';
import {isHelpContextEqual} from '../configeditor/isHelpContextEqual';

interface ConfigEditorHelpProps {
  context: ConfigEditorHelpContext | null;
  allInnerTypes: TypeData[];
}

export const ConfigEditorHelp = memo(
  ({context, allInnerTypes}: ConfigEditorHelpProps) => {
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
  border-top: 1px solid ${Colors.keylineDefault()};
  background: ${Colors.backgroundLight()};
  color: ${Colors.textLight()};
`;

const ConfigScrollWrap = styled.div`
  padding: 8px;
  color: ${Colors.textDefault()};
  flex: 1;
  pointer-events: initial;
  max-height: 100%;
  overflow-y: auto;
`;

const Container = styled.div`
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: ${Colors.backgroundLight()};
  height: 100%;
`;
