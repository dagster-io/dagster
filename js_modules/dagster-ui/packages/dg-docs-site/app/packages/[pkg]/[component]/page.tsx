import getContents, {getComponent} from '@/util/getContents';
import ComponentDetails from '@dagster-io/dg-docs-components/ComponentDetails';

import styles from './css/ComponentPage.module.css';

interface Props {
  params: Promise<{pkg: string; component: string}>;
}

export default async function ComponentPage({params}: Props) {
  const {pkg, component} = await params;
  const contents = await getContents();
  if (!contents) {
    return <div>Contents not found</div>;
  }

  const componentConfig = await getComponent(contents, pkg, component);
  if (!componentConfig) {
    return <div>Component not found</div>;
  }

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
              Example <code>component.yaml</code>
            </a>
          </li>
        </ol>
      </div>
    </div>
  );
}

export async function generateStaticParams() {
  const contents = await getContents();
  if (!contents) {
    return [];
  }
  return contents
    .map((pkg) => {
      return pkg.componentTypes.map(({name}) => ({
        pkg: pkg.name,
        component: name,
      }));
    })
    .flat();
}
