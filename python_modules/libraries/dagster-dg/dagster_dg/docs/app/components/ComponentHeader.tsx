import {ComponentType} from '@/util/types';

import styles from './css/ComponentHeader.module.css';
import ComponentTags from '@/app/components/ComponentTags';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import stripMarkdown from 'strip-markdown';

interface Props {
  config: ComponentType;
  descriptionStyle: 'plaintext' | 'markdown';
}

export default function ComponentHeader({config, descriptionStyle}: Props) {
  return (
    <div className={styles.container}>
      <div className={styles.heading}>
        <div className={styles.icon} />
        <div className={styles.headingContent}>
          <h1>{config.name}</h1>
          <div className={styles.description}>
            <Markdown
              remarkPlugins={descriptionStyle === 'markdown' ? [remarkGfm] : [stripMarkdown]}
            >
              {config.description}
            </Markdown>
          </div>
        </div>
      </div>
      {config.tags.length > 0 ? <ComponentTags author={config.author} tags={config.tags} /> : null}
    </div>
  );
}
