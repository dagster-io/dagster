import {MyImage} from '../../components/markdoc/Image';

export const image = {
  render: MyImage,
  children: ['inline'],
  attributes: {
    src: {type: String},
    alt: {type: String},
    title: {type: String},
  },
};
