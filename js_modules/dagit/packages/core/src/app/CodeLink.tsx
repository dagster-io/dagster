import {Icon, ExternalAnchorButton} from '@dagster-io/ui';
import * as React from 'react';

import {AppContext} from './AppContext';
import {CodeLinkProtocolContext} from './CodeLinkProtocol';

export const CodeLink: React.FC<{file: string; lineNumber: number}> = ({file, lineNumber}) => {
  const {codeLinksEnabled} = React.useContext(AppContext);
  const [codeLinkProtocol, _] = React.useContext(CodeLinkProtocolContext);

  if (!codeLinksEnabled) {
    return null;
  }

  const codeLink = codeLinkProtocol.protocol
    .replace('{FILE}', file)
    .replace('{LINE}', lineNumber.toString());
  return (
    <ExternalAnchorButton icon={<Icon name="open_in_new" />} href={codeLink}>
      Open in editor
    </ExternalAnchorButton>
  );
};
