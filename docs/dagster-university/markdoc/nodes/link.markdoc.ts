import {Tag, nodes} from '@markdoc/markdoc';
import Link from 'next/link';

export const link = {
  render: Link,
  attributes: nodes.link.attributes,
  transform(node, config) {
    const attributes = node.transformAttributes(config);
    const children = node.transformChildren(config);
    const {href} = attributes;

    // If the link is to another site, open in a new window.
    return new Tag(
      this.render,
      {...attributes, target: href.startsWith('http') ? '_blank' : undefined},
      children,
    );
  },
};
