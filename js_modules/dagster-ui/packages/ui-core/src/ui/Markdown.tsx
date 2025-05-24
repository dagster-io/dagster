import {Colors, FontFamily} from '@dagster-io/ui-components';
import styles from './Markdown.module.css';

import {lazy} from '../util/lazy';

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

