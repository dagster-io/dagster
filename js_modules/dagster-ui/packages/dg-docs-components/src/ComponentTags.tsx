import clsx from 'clsx';

import styles from './css/ComponentTags.module.css';

export default function ComponentTags({author, tags}: {author: string; tags: string[]}) {
  return (
    <div className={styles.tags}>
      {author ? <div className={clsx(styles.tag, styles.authorTag)}>author: {author}</div> : null}
      {tags.map((tag) => (
        <div key={tag} className={styles.tag}>
          tag: {tag}
        </div>
      ))}
    </div>
  );
}
