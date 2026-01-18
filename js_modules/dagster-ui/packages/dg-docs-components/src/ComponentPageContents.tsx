import ComponentDetails from './ComponentDetails';
import {ComponentType} from './types';

import styles from './css/ComponentPageContents.module.css';

interface Props {
  componentConfig: ComponentType;
}
export default function ComponentPageContents({componentConfig}: Props) {
  return (
    <div className={styles.outer}>
      <div className={styles.container}>
        <div className={styles.main}>
          <ComponentDetails config={componentConfig} />
        </div>
      </div>
      <div className={styles.tableOfContents}>
        <ol>
          <li>
            <a href="#scaffolding">Scaffolding</a>
          </li>
          <li>
            <a href="#schema">Schema</a>
          </li>
          <li>
            <a href="#example">
              Example <code>defs.yaml</code>
            </a>
          </li>
        </ol>
      </div>
    </div>
  );
}
