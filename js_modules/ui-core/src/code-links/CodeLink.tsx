import {Box, Icon, IconName, MiddleTruncate, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {CodeLinkProtocolContext, ProtocolData} from './CodeLinkProtocol';
import {assertUnreachable} from '../app/Util';
import {SourceLocation} from '../graphql/types';

const getCodeReferenceIcon = (codeReference: SourceLocation): IconName => {
  switch (codeReference.__typename) {
    case 'LocalFileCodeReference':
      return 'code_block';
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
        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}} style={{whiteSpace: 'nowrap'}}>
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
        .replace('{LINE}', (codeReference.lineNumber || 1).toString());
    case 'UrlCodeReference':
      return codeReference.url;
    default:
      assertUnreachable(codeReference);
  }
};

export const getCodeReferenceKey = (codeReference: SourceLocation): string => {
  switch (codeReference.__typename) {
    case 'LocalFileCodeReference':
      return `${codeReference.filePath}:${codeReference.lineNumber}`;
    case 'UrlCodeReference':
      return codeReference.url;
    default:
      assertUnreachable(codeReference);
  }
};

export const getCodeReferenceTooltip = (codeReference: SourceLocation): string => {
  switch (codeReference.__typename) {
    case 'LocalFileCodeReference':
      return `Open in editor`;
    case 'UrlCodeReference':
      if (codeReference.url.includes('github')) {
        return `Open in GitHub`;
      } else {
        return `Open in GitLab`;
      }
    default:
      assertUnreachable(codeReference);
  }
};

export const CodeLink = ({sourceLocation}: {sourceLocation: SourceLocation}) => {
  const [codeLinkProtocol, _] = React.useContext(CodeLinkProtocolContext);

  return (
    <Box style={{minWidth: 0}} flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Icon name={getCodeReferenceIcon(sourceLocation)} />
      <a
        target="_blank"
        rel="noreferrer"
        style={{minWidth: 0}}
        href={getCodeReferenceLink(codeLinkProtocol, sourceLocation)}
      >
        <Tooltip
          display="block"
          content={getCodeReferenceTooltip(sourceLocation)}
          position="bottom"
        >
          {getCodeReferenceEntryLabel(sourceLocation)}
        </Tooltip>
      </a>
      <Icon name="open_in_new" />
    </Box>
  );
};
