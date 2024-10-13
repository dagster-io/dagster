import {Meta} from '@storybook/react';

import {IOpTag, KNOWN_TAGS, OpTags} from '../OpTags';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'OpTags',
  component: OpTags,
} as Meta;

export const AllTags = () => {
  const tags: IOpTag[] = Object.keys(KNOWN_TAGS).map((label) => ({label, onClick: () => {}}));
  return (
    <div style={{height: '600px', position: 'relative'}}>
      <OpTags tags={tags} style={{flexWrap: 'wrap'}} />
    </div>
  );
};
