import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ConfigTypeSchema, TypeData} from 'src/ConfigTypeSchema';
import {ConfigEditorHelpContext, isHelpContextEqual} from 'src/configeditor/ConfigEditor';

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

export const ConfigEditorHelpConfigTypeFragment = gql`
  fragment ConfigEditorHelpConfigTypeFragment on ConfigType {
    ...ConfigTypeSchemaFragment
  }
  ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
`;

const AutocompletionsNote = styled.div`
  font-size: 0.75rem;
  text-align: center;
  padding: 4px;
  border-top: 1px solid ${Colors.LIGHT_GRAY1};
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
