import {HTMLProps} from 'react';
import Markdown, {Components} from 'react-markdown';
import remarkGfm from 'remark-gfm';

import styles from './css/ComponentHeader.module.css';

import ComponentTags from './ComponentTags';
import {ComponentType} from './types';

interface Props {
  config: ComponentType;
  descriptionStyle: 'truncated' | 'full';
}

export default function ComponentHeader({config, descriptionStyle}: Props) {
  const {description, name} = config;

  // For truncated display, use only the first line in the description.
  const displayedDescription =
    descriptionStyle === 'truncated'
      ? (description.split('\n').find((str) => str.trim().length > 0) ?? '')
      : description;

  return (
    <div className={styles.container}>
      <div className={styles.heading}>
        <div className={styles.icon} />
        <div className={styles.headingContent}>
          <h1>{name}</h1>
          <div className={styles.description}>
            <Markdown
              remarkPlugins={[remarkGfm]}
              components={descriptionStyle === 'truncated' ? componentsMinusLinks : undefined}
            >
              {displayedDescription}
            </Markdown>
          </div>
        </div>
      </div>
      {config.tags.length > 0 ? <ComponentTags author={config.author} tags={config.tags} /> : null}
    </div>
  );
}

const componentsMinusLinks: Components = {
  a: ({children}: HTMLProps<HTMLAnchorElement>) => <span>{children}</span>,
};
