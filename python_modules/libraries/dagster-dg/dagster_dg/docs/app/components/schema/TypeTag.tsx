import clsx from 'clsx';
import styles from './css/TypeTag.module.css';
import {JSONSchema7TypeName} from 'json-schema';

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
    <button
      className={clsx(
        styles.tag,
        !basicTypes.has(name as JSONSchema7TypeName) ? styles.objectType : null,
      )}
    >
      {name}
    </button>
  );
}
