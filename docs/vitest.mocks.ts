import React from 'react';

// Mock for @theme/CodeBlock
const CodeBlock = (props: any) => {
  return React.createElement('pre', {}, props.children);
};

// Mock for code-examples-content
export const CODE_EXAMPLE_PATH_MAPPINGS: Record<string, any> = {};

export default CodeBlock;
