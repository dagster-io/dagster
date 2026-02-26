import hljs from 'highlight.js/lib/core';
import hljsYaml from 'highlight.js/lib/languages/yaml';

import CopyButton from './CopyButton';
import styles from './css/ComponentExample.module.css';

import './css/yaml.css';

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
        <CopyButton content={yaml} />
      </div>
    </div>
  );
}
