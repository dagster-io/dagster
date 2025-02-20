/**
 * Custom admonition linking to code examples in the GitHub repository.
 *
 * Versioning is inferred from the version label using `useDocsPreferredVersion`.
 */

import React from 'react';
import Admonition from '@theme/Admonition';
import {useDocsPreferredVersion} from '@docusaurus/theme-common';


export const CodeReferenceLink = ({filePath, isInline, children}) => {
  const preferredVersionLabel = useDocsPreferredVersion('default').preferredVersion?.label;
  const siteVersion = preferredVersionLabel ? preferredVersionLabel.match(/^\d+\.\d+\.\d+/)?.[0] || 'master' : 'master';
  const url = `https://github.com/dagster-io/dagster/tree/${siteVersion}/${filePath}`;

  if (isInline) {
    return <a href={url}>{children}</a>;
  } else {
    return (
      <Admonition type="tip" title="Title">
        You can find the code for this example on <a href={url}>GitHub</a>.
      </Admonition>
    );
  }
};
