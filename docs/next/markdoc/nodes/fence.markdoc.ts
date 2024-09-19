import {nodes} from '@markdoc/markdoc';

import {Fence} from '../../components/markdoc/FencedCodeBlock';

export const fence = {
  render: Fence,
  attributes: nodes.fence.attributes,
};
