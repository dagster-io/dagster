import {nodes} from '@markdoc/markdoc';
import {CodeBlock} from '../../components';

export const fence = {
  render: CodeBlock,
  attributes: {
    obfuscated: {
      type: Boolean,
    },
    ...nodes.fence.attributes,
  },
};
