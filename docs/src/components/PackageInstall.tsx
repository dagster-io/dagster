import React from 'react';
import CodeBlock from '@theme/CodeBlock';
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

export const PackageInstallInstructions: React.FunctionComponent<{packageName: string}> = ({packageName}) => {
  const uvCommand = `uv add ${packageName}`;
  const pipCommand = `pip install ${packageName}`;

  return (
    <Tabs>
      <TabItem value="uv" label="uv">
        <CodeBlock language="shell">{uvCommand || 'Loading...'}</CodeBlock>
      </TabItem>
      <TabItem value="pip" label="pip">
        <CodeBlock language="shell">{pipCommand || 'Loading...'}</CodeBlock>
      </TabItem>
    </Tabs>
  );
};
