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

export const VersionControlCodeLink = ({
  versionControlUrl,
  pathInModule,
  lineNumber,
}: {
  versionControlUrl: string;
  pathInModule: string;
  lineNumber: number;
}) => {
  const codeLink = versionControlUrl + '/' + pathInModule + '#L' + lineNumber.toString();

  if (versionControlUrl.includes('github.com')) {
    return (
      <ExternalAnchorButton icon={<Icon name="github" />} href={codeLink}>
        Open in GitHub
      </ExternalAnchorButton>
    );
  } else if (versionControlUrl.includes('gitlab.com')) {
    return (
      <ExternalAnchorButton icon={<Icon name="gitlab" />} href={codeLink}>
        Open in GitLab
      </ExternalAnchorButton>
    );
  }
  return (
    <ExternalAnchorButton icon={<Icon name="open_in_new" />} href={codeLink}>
      Open source
    </ExternalAnchorButton>
  );
};
