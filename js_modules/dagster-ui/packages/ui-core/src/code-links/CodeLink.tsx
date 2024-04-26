import {Box, Menu, MenuItem, Popover} from '@dagster-io/ui-components';
import {Button, ExternalAnchorButton} from '@dagster-io/ui-components/src/components/Button';
import {Icon} from '@dagster-io/ui-components/src/components/Icon';
import * as React from 'react';

import {CodeLinkProtocolContext, ProtocolData} from './CodeLinkProtocol';
import {CodeReferencesMetadataEntry, SourceLocation} from '../graphql/types';

const getCodeReferenceEntryLabel = (codeReference: SourceLocation): string => {
  return codeReference.label || (codeReference.filePath.split('/').pop() as string);
};

const getCodeReferenceLink = (
  codeLinkProtocol: ProtocolData,
  codeReference: SourceLocation,
): string => {
  return codeLinkProtocol.protocol
    .replace('{FILE}', codeReference.filePath)
    .replace('{LINE}', codeReference.lineNumber.toString());
};

export const CodeLink = ({codeLinkData}: {codeLinkData: CodeReferencesMetadataEntry}) => {
  const [codeLinkProtocol, _] = React.useContext(CodeLinkProtocolContext);

  const sources = codeLinkData.codeReferences;

  const hasMultipleCodeSources = sources.length > 1;

  return (
    <Box flex={{alignItems: 'center'}}>
      {hasMultipleCodeSources ? (
        <Popover
          position="bottom-right"
          content={
            <Menu>
              {sources.map((source) => (
                <MenuItem
                  key={`${source.filePath}:${source.lineNumber}`}
                  text={getCodeReferenceEntryLabel(source)}
                  onClick={() => {
                    const codeLink = getCodeReferenceLink(codeLinkProtocol, source);
                    window.open(codeLink, '_blank');
                  }}
                />
              ))}
            </Menu>
          }
        >
          <Button
            icon={<Icon name="expand_more" />}
            style={{
              minWidth: 'initial',
              borderTopLeftRadius: 0,
              borderBottomLeftRadius: 0,
              marginLeft: '-1px',
            }}
          >
            Open in editor
          </Button>
        </Popover>
      ) : (
        <ExternalAnchorButton
          icon={<Icon name="open_in_new" />}
          href={getCodeReferenceLink(codeLinkProtocol, sources[0] as SourceLocation)}
          style={
            hasMultipleCodeSources
              ? {
                  borderTopRightRadius: 0,
                  borderBottomRightRadius: 0,
                  borderRight: '0px',
                }
              : {}
          }
        >
          Open {getCodeReferenceEntryLabel(sources[0] as SourceLocation)} in editor
        </ExternalAnchorButton>
      )}
    </Box>
  );
};
