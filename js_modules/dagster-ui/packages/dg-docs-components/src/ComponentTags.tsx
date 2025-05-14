import clsx from 'clsx';

import styles from './css/ComponentTags.module.css';

export default function ComponentTags({owners, tags}: {owners: string[]; tags: string[]}) {
  return (
    <div className={styles.tags}>
      {owners.map((owner) => (
        <div key={owner} className={clsx(styles.tag, styles.authorTag)}>
         owner: {owner}
        </div>
      ))}
      {tags.map((tag) => (
        <div key={tag} className={styles.tag}>
          tag: {tag}
        </div>
      ))}
    </div>
  );
}
