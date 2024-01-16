import {Code} from '../../components/markdoc/Code';

export const fence = {
  render: Code,
  attributes: {
    language: {type: String},
    dagimage: {type: String},
    fullwidth: {type: Boolean},
  },
};
