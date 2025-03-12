import clsx from 'clsx';
import styles from './css/TypeTag.module.css';

interface Props {
  name: string;
  onClick?: () => void;
}

export default function TypeTag({name, onClick}: Props) {
  return (
    <button className={clsx(styles.tag, onClick ? styles.clickable : null)} onClick={onClick}>
      {name}
    </button>
  );
}
