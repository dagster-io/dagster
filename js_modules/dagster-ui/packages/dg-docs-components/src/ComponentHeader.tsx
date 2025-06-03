import {HTMLProps, useMemo} from 'react';
import Markdown, {Components} from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {remark} from 'remark';
import styles from './css/ComponentHeader.module.css';
import strip from 'strip-markdown';

import ComponentTags from './ComponentTags';
import {ComponentType} from './types';

interface Props {
  config: ComponentType;
  descriptionStyle: 'truncated' | 'full';
}

export default function ComponentHeader({config, descriptionStyle}: Props) {
  const {description, name} = config;

  // For truncated display, use only the first text block in the description.
  const displayedDescription = useMemo(
    () =>
      descriptionStyle === 'truncated'
        ? (markdownToPlaintext(description || '')
            .split('\n\n')
            .find((str) => str.trim().length > 0) ?? '')
        : description,
    [descriptionStyle, description],
  );

  return (
    <div className={styles.container}>
      <div className={styles.heading}>
        <svg
          className={styles.icon}
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="currentColor"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M9.16667 16.1875V10.4791L4.16667 7.58329V13.2916L9.16667 16.1875ZM10.8333 16.1875L15.8333 13.2916V7.58329L10.8333 10.4791V16.1875ZM10 9.04163L14.9375 6.18746L10 3.33329L5.0625 6.18746L10 9.04163ZM3.33333 14.75C3.06944 14.5972 2.86458 14.3958 2.71875 14.1458C2.57292 13.8958 2.5 13.618 2.5 13.3125V6.68746C2.5 6.3819 2.57292 6.10413 2.71875 5.85413C2.86458 5.60413 3.06944 5.40274 3.33333 5.24996L9.16667 1.89579C9.43056 1.74301 9.70833 1.66663 10 1.66663C10.2917 1.66663 10.5694 1.74301 10.8333 1.89579L16.6667 5.24996C16.9306 5.40274 17.1354 5.60413 17.2812 5.85413C17.4271 6.10413 17.5 6.3819 17.5 6.68746V13.3125C17.5 13.618 17.4271 13.8958 17.2812 14.1458C17.1354 14.3958 16.9306 14.5972 16.6667 14.75L10.8333 18.1041C10.5694 18.2569 10.2917 18.3333 10 18.3333C9.70833 18.3333 9.43056 18.2569 9.16667 18.1041L3.33333 14.75Z"
            fill="currentColor"
          />
        </svg>
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
      {config.tags && config.tags.length > 0 ? (
        <ComponentTags owners={config.owners} tags={config.tags} />
      ) : null}
    </div>
  );
}

const componentsMinusLinks: Components = {
  a: ({children}: HTMLProps<HTMLAnchorElement>) => <span>{children}</span>,
};

const Remark = remark().use(strip);

export const markdownToPlaintext = (md: string) => {
  return Remark.processSync(md).toString().replace(/\\/g, '').trim();
};
