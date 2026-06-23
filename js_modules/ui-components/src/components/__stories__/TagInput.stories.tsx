import {useState} from 'react';

import {TagInput} from '../TagInput';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TagInput',
  component: TagInput,
};

export const Default = () => {
  const [values, setValues] = useState<string[]>([]);
  return (
    <TagInput values={values} onChange={(next) => setValues(next)} placeholder="Type a tag…" />
  );
};

export const WithAddMenu = () => {
  const [values, setValues] = useState<string[]>([]);
  return (
    <TagInput
      values={values}
      onChange={(next) => setValues(next)}
      showAddMenu
      placeholder="Type a tag…"
    />
  );
};

export const EmailInput = () => {
  const [values, setValues] = useState<string[]>([]);
  return (
    <TagInput values={values} onChange={(next) => setValues(next)} placeholder="email@domain.com" />
  );
};

const isValidTag = (v: string) => v.includes(':');

export const WithIntentValidation = () => {
  const [values, setValues] = useState<string[]>(['valid:tag', 'bad']);
  return (
    <TagInput
      values={values}
      onChange={(next) => setValues(next)}
      showAddMenu
      placeholder="team:ml"
      tagProps={(value) => (isValidTag(value) ? {} : {intent: 'danger'})}
    />
  );
};
