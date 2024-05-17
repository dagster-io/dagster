import {Box, Menu, MiddleTruncate, Popover, Tooltip} from '@dagster-io/ui-components';
import {Button, ExternalAnchorButton} from '@dagster-io/ui-components/src/components/Button';
import {Icon, IconName} from '@dagster-io/ui-components/src/components/Icon';
import * as React from 'react';

import {CodeLinkProtocolContext, ProtocolData} from './CodeLinkProtocol';
import {assertUnreachable} from '../app/Util';
import {CodeReferencesMetadataEntry, SourceLocation} from '../graphql/types';
import {MenuLink} from '../ui/MenuLink';

const getCodeReferenceIcon = (codeReference: SourceLocation): IconName => {
  switch (codeReference.__typename) {
    case 'LocalFileCodeReference':
      return 'open_in_new';
    case 'UrlCodeReference':
      return codeReference.url.includes('github') ? 'github' : 'gitlab';
    default:
      assertUnreachable(codeReference);
  }
};

const getCodeReferenceEntryLabel = (codeReference: SourceLocation): React.ReactElement => {
  switch (codeReference.__typename) {
    case 'LocalFileCodeReference':
      const label = codeReference.label || (codeReference.filePath.split('/').pop() as string);
      return (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
          Open <MiddleTruncate text={label} /> in editor
        </Box>
      );
    case 'UrlCodeReference':
      const labelOrUrl =
        codeReference.label || (codeReference.url.split('/').pop()?.split('#')[0] as string);
      const sourceControlName = codeReference.url.includes('github') ? 'GitHub' : 'GitLab';
      return (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
          Open <MiddleTruncate text={labelOrUrl} /> in {sourceControlName}
        </Box>
      );
    default:
      assertUnreachable(codeReference);
  }
};

const getCodeReferenceLink = (
  codeLinkProtocol: ProtocolData,
  codeReference: SourceLocation,
): string => {
  switch (codeReference.__typename) {
    case 'LocalFileCodeReference':
      return codeLinkProtocol.protocol
        .replace('{FILE}', codeReference.filePath)
        .replace('{LINE}', codeReference.lineNumber.toString());
    case 'UrlCodeReference':
      return codeReference.url;
    default:
      assertUnreachable(codeReference);
  }
};

const getCodeReferenceKey = (codeReference: SourceLocation): string => {
  switch (codeReference.__typename) {
    case 'LocalFileCodeReference':
      return `${codeReference.filePath}:${codeReference.lineNumber}`;
    case 'UrlCodeReference':
      return codeReference.url;
    default:
      assertUnreachable(codeReference);
  }
};

export const CodeLink = ({codeLinkData}: {codeLinkData: CodeReferencesMetadataEntry}) => {
  const [codeLinkProtocol, _] = React.useContext(CodeLinkProtocolContext);

  const sources = codeLinkData.codeReferences;

  const hasMultipleCodeSources = sources.length > 1;
  const firstSource = sources[0] as SourceLocation;

  return (
    <Box flex={{alignItems: 'center'}}>
      {hasMultipleCodeSources ? (
        <Popover
          position="bottom-right"
          content={
            <Menu>
              {sources.map((source) => (
                <Tooltip
                  key={getCodeReferenceKey(source)}
                  content={getCodeReferenceLink(codeLinkProtocol, source)}
                  position="bottom"
                  display="block"
                >
                  <MenuLink
                    text={getCodeReferenceEntryLabel(source)}
                    to={getCodeReferenceLink(codeLinkProtocol, source)}
                    icon={<Icon name={getCodeReferenceIcon(source)} />}
                    style={{maxWidth: 300}}
                  />
                </Tooltip>
              ))}
            </Menu>
          }
        >
          <Button rightIcon={<Icon name="expand_more" />}>Open source code</Button>
        </Popover>
      ) : (
        <Tooltip content={getCodeReferenceLink(codeLinkProtocol, firstSource)} position="bottom">
          <ExternalAnchorButton
            icon={<Icon name={getCodeReferenceIcon(firstSource)} />}
            href={getCodeReferenceLink(codeLinkProtocol, firstSource)}
            style={{maxWidth: 300}}
          >
            {getCodeReferenceEntryLabel(firstSource)}
          </ExternalAnchorButton>
        </Tooltip>
      )}
    </Box>
  );
};
