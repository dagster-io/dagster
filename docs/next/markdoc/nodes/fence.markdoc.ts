import {nodes} from '@markdoc/markdoc';

import {Code} from '../../components/markdoc/Code';

export const fence = {
  render: Code,
  attributes: nodes.fence.attributes,
};
