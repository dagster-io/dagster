import styles from './css/ComponentDetails.module.css';

import ComponentExample from './ComponentExample';
import ComponentHeader from './ComponentHeader';
import ComponentScaffolding from './ComponentScaffolding';
import ComponentSchema from './ComponentSchema';
import {ComponentType} from './types';

interface Props {
  config: ComponentType;
}

export default function ComponentDetails({config}: Props) {
  return (
    <div>
      <ComponentHeader config={config} descriptionStyle="full" />
      <div className={styles.sectionHeader} id="scaffolding">
        <h2>Scaffolding</h2>
        <a href="#scaffolding">#</a>
      </div>
      <ComponentScaffolding componentName={config.name} />
      <div className={styles.sectionHeader} id="schema">
        <h2>Schema</h2>
        <a href="#schema">#</a>
      </div>
      <ComponentSchema schema={config.schema} />
      <div className={styles.sectionHeader} id="example">
        <h2>
          Example <code>component.yaml</code>
        </h2>
        <a href="#example">#</a>
      </div>
      <ComponentExample yaml={config.example} />
    </div>
  );
}
