import getContents from '../util/getContents';
import styles from './css/page.module.css';
import ComponentHeader from '@dagster-io/dg-docs-components/ComponentHeader';
import Link from 'next/link';

export default async function Home() {
  const contents = await getContents();

  if (!contents) {
    return <div>Contents not found</div>;
  }

  const allComponents = contents
    .map((pkg) => {
      return pkg.componentTypes.map((component) => ({
        component,
        packageName: pkg.name,
      }));
    })
    .flat();

  return (
    <div className={styles.container}>
      {allComponents.map(({component, packageName}) => (
        <Link
          href={`/packages/${packageName}/${component.name}`}
          key={component.name}
          className={styles.componentItem}
        >
          <ComponentHeader config={component} descriptionStyle="truncated" />
        </Link>
      ))}
    </div>
  );
}
