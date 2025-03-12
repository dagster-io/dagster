import hljs from 'highlight.js/lib/core';
import hljsYaml from 'highlight.js/lib/languages/yaml';
import styles from './css/ComponentExample.module.css';
import './css/yaml.css';
import CopyButton from '@/app/components/CopyButton';
import {Suspense} from 'react';

hljs.registerLanguage('yaml', hljsYaml);

interface Props {
  yaml: string;
}

export default function ComponentExample({yaml}: Props) {
  const highlightedYaml = hljs.highlight(yaml, {language: 'yaml'}).value;
  return (
    <div className={styles.container}>
      <pre dangerouslySetInnerHTML={{__html: highlightedYaml}} className={styles.code} />
      <div className={styles.buttonContainer}>
        <Suspense fallback={<div />}>
          <CopyButton content={yaml} />
        </Suspense>
      </div>
    </div>
  );
}
