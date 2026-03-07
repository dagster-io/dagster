import {JSONSchema7, JSONSchema7Definition} from 'json-schema';

import styles from './css/ArrayTag.module.css';

interface Props {
  items: JSONSchema7['items'];
  defs: Record<string, JSONSchema7Definition> | undefined;
}

export default function ArrayTag({items, defs}: Props) {
  const itemName = getItemName(items, defs);
  return <div className={styles.tag}>Array&lt;{itemName}&gt;</div>;
}

function getItemName(
  items: JSONSchema7['items'],
  defs: Record<string, JSONSchema7Definition> | undefined,
): string {
  if (items === undefined) {
    return 'undefined';
  }

  if (items === true) {
    return 'true';
  }

  if (items === false) {
    return 'false';
  }

  if (Array.isArray(items)) {
    return items
      .map((item) => getItemName(item, defs))
      .flat()
      .join(' | ');
  }

  if (items.$ref) {
    const refName = items.$ref.split('/').pop();
    if (refName) {
      return refName;
    }
    return 'unknown';
  }

  const type = items.type;
  if (type && typeof type === 'string') {
    return type;
  }

  return 'Array';
}
