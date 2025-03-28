import CopyButton from './CopyButton';
import styles from './css/ComponentScaffolding.module.css';

export default function ComponentScaffolding({componentName}: {componentName: string}) {
  const command = `dg scaffold component ${componentName} {component_name}`;
  return (
    <div className={styles.container}>
      <div>
        Use the scaffolding command to generate the necessary files and configuration for your
        component.
      </div>
      <div className={styles.commandContainer}>
        <pre>{command}</pre>
        <div className={styles.buttonContainer}>
          <CopyButton content={command} />
        </div>
      </div>
    </div>
  );
}
