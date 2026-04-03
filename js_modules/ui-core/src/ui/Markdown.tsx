import {lazy} from '../util/lazy';
import styles from './css/Markdown.module.css';

const MarkdownWithPlugins = lazy(() => import('./MarkdownWithPlugins'));

interface Props {
  children: string;
}

export const Markdown = (props: Props) => {
  return (
    <div className={styles.container}>
      <MarkdownWithPlugins {...props} />
    </div>
  );
};
