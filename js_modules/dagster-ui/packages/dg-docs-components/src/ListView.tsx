import {HTMLProps, ReactNode} from 'react';
import {Contents} from './types';
import ComponentHeader from './ComponentHeader';
import styles from './css/ListView.module.css';

interface Props {
  contents: Contents | null;
  loading: boolean;
  renderLink: (props: HTMLProps<HTMLAnchorElement>) => ReactNode;
}

export default function ListView({contents, renderLink, loading}: Props) {
  if (loading) {
    return <div className={styles.emptyState}>Loading…</div>;
  }

  if (!contents) {
    return <div className={styles.emptyState}>No components found.</div>;
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
      {allComponents.map(({component, packageName}) =>
        renderLink({
          key: component.name,
          href: `/packages/${packageName}/${component.name}`,
          className: styles.componentItem,
          children: <ComponentHeader config={component} descriptionStyle="truncated" />,
        }),
      )}
    </div>
  );
}
