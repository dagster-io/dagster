import {Fence} from '../../components/markdoc/FencedCodeBlock';

export const fence = {
  render: Fence,
  attributes: {
    language: {
      type: String,
    },
  },
};
