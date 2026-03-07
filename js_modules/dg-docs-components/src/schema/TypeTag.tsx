import clsx from 'clsx';
import {JSONSchema7TypeName} from 'json-schema';

import styles from './css/TypeTag.module.css';

const basicTypes = new Set<JSONSchema7TypeName>([
  'string',
  'number',
  'boolean',
  'object',
  'array',
  'null',
]);

interface Props {
  name: string;
}

export default function TypeTag({name}: Props) {
  return (
    <span
      className={clsx(
        styles.tag,
        !basicTypes.has(name as JSONSchema7TypeName) ? styles.objectType : null,
      )}
    >
      {name}
    </span>
  );
}
