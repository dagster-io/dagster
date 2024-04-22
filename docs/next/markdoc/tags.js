import {Button} from '../components/markdoc/Button';
import {Note, Warning} from '../components/markdoc/Callouts';

export const note = {
  render: Note,
};

export const warning = {
  render: Warning,
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
};
