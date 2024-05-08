import {ExternalAnchorButton} from '@dagster-io/ui-components/src/components/Button';
import {Icon} from '@dagster-io/ui-components/src/components/Icon';
import * as React from 'react';

import {CodeLinkProtocolContext} from './CodeLinkProtocol';

export const CodeLink = ({file, lineNumber}: {file: string; lineNumber: number}) => {
  const [codeLinkProtocol, _] = React.useContext(CodeLinkProtocolContext);

  const codeLink = codeLinkProtocol.protocol
    .replace('{FILE}', file)
    .replace('{LINE}', lineNumber.toString());
  return (
    <ExternalAnchorButton icon={<Icon name="open_in_new" />} href={codeLink}>
      Open in editor
    </ExternalAnchorButton>
  );
};
