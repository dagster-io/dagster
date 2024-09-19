import {Tag} from '@markdoc/markdoc';
import GithubSlugger from 'github-slugger';

import {Heading} from '../../components/Heading';

function generateID(children, attributes) {
  if (attributes.id && typeof attributes.id === 'string') {
    return attributes.id;
  }
  const headingStr = children.find((child) => typeof child === 'string');
  const slugger = new GithubSlugger();
  return slugger.slug(headingStr);
}

export const heading = {
  render: Heading,
  children: ['inline'],
  attributes: {
    id: {type: String},
    level: {type: Number, required: true, default: 1},
    className: {type: String},
  },
  transform(node, config) {
    const attributes = node.transformAttributes(config);
    const children = node.transformChildren(config);
    const id = generateID(children, attributes);

    return new Tag(this.render, {...attributes, id}, children);
  },
};
