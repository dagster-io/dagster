import {Tag} from '@markdoc/markdoc';

import {Button, ButtonContainer} from '../components/markdoc/Button';
import {Note, Warning} from '../components/markdoc/Callouts';
import {Check, Cross} from '../components/markdoc/CheckCross';

export const note = {
  render: Note,
};

export const warning = {
  render: Warning,
};

export const buttonContainer = {
  render: ButtonContainer,
};

export const button = {
  render: Button,
  children: ['text'],
  attributes: {
    link: {
      type: String,
    },
    style: {
      type: String,
      default: 'primary',
      matches: ['primary', 'secondary', 'blurple'],
    },
  },
  transform(node, config) {
    console.log(node);
    console.log(config);
    const attributes = node.transformAttributes(config);
    const children = node.transformChildren(config);
    console.log(attributes);
    console.log(children);
    return new Tag('Button', attributes, children);
  },
};

export const check = {
  render: Check,
  selfClosing: true,
};

export const cross = {
  render: Cross,
  selfClosing: true,
};
