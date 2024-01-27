import {ExternalAnchorButton} from '@dagster-io/ui-components/src/components/Button';
import {Icon} from '@dagster-io/ui-components/src/components/Icon';
import * as React from 'react';

import {CodeLinkProtocolContext} from './CodeLinkProtocol';
import {AppContext} from '../app/AppContext';

export const CodeLink = ({file, lineNumber}: {file: string; lineNumber: number}) => {
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
