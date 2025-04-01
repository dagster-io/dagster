'use client';

import clsx from 'clsx';
import {JSONSchema7, JSONSchema7Definition, JSONSchema7TypeName} from 'json-schema';
import {useState} from 'react';

import styles from './css/ComponentSchema.module.css';
import ArrayTag from './schema/ArrayTag';
import TypeTag from './schema/TypeTag';

interface Props {
  schema: string;
}

export default function ComponentSchema({schema}: Props) {
  let json;
  try {
    json = JSON.parse(schema);
  } catch (error) {
    console.error(error);
  }

  if (!json) {
    return <div>Invalid schema</div>;
  }

  const jsonSchema: JSONSchema7 = json;
  return <SchemaRoot schema={jsonSchema} defs={jsonSchema.$defs} />;
}

function SchemaRoot({
  schema,
  defs,
}: {
  schema: JSONSchema7;
  defs: Record<string, JSONSchema7Definition> | undefined;
}) {
  const title = schema.title;
  const properties = schema.properties ?? {};

  return (
    <div className={styles.schemaContainer}>
      {title ? <div className={styles.schemaTitle}>{title}</div> : null}
      {Object.entries(properties).map(([key, property]) => (
        <Property key={key} name={key} property={property} defs={defs} />
      ))}
    </div>
  );
}

function Property({
  name,
  property,
  defs,
}: {
  name: string;
  property: JSONSchema7Definition;
  defs: Record<string, JSONSchema7Definition> | undefined;
}) {
  const [expanded, setExpanded] = useState(false);

  const onToggleExpansion = () => {
    setExpanded((current) => !current);
  };

  if (property === true || property === false) {
    return null;
  }

  const {anyOf, type, description, default: defaultValue, $ref, required, examples} = property;

  const expandable = isExpandableProperty(property);

  const firstExample = examples ? (Array.isArray(examples) ? examples[0] : examples) : null;

  return (
    <div className={styles.propertyContainer}>
      <button
        disabled={!expandable}
        className={clsx(styles.expandButton, expanded && styles.expanded)}
        onClick={onToggleExpansion}
      >
        <div className={styles.property}>
          <div className={styles.propertyNameAndTypes}>
            <div className={styles.propertyName}>{name}</div>
            {$ref ? <PropertyRef ref={$ref} defs={defs} /> : null}
            {type ? <PropertyType property={property} defs={defs} /> : null}
            {anyOf ? <PropertyAnyOf anyOf={anyOf} defs={defs} /> : null}
            {required ? <div className={styles.required}>required</div> : null}
          </div>
          {expandable ? (
            <div className={styles.chevronContainer}>
              <Chevron />
            </div>
          ) : null}
        </div>
        {description || defaultValue || examples ? (
          <div className={styles.propertyDescriptionContainer}>
            <div className={styles.propertyDescription}>{description}</div>
            {defaultValue ? (
              <div className={styles.propertyDefault}>
                default:{' '}
                <div className={styles.propertyDefaultValue}>{JSON.stringify(defaultValue)}</div>
              </div>
            ) : null}
            {firstExample ? (
              <div className={styles.propertyExamples}>
                example:{' '}
                <div className={styles.propertyExamplesValue}>{JSON.stringify(firstExample)}</div>
              </div>
            ) : null}
          </div>
        ) : null}
      </button>
      {expanded ? (
        <div className={styles.expansionContainer}>
          <ExpandedRoot property={property} defs={defs} />
        </div>
      ) : null}
    </div>
  );
}

function isExpandableProperty(property: JSONSchema7): boolean {
  const {type, anyOf, $ref} = property;

  if ($ref) {
    return true;
  }

  if (type === 'array') {
    const {items} = property;
    if (items === undefined || items === true || items === false) {
      return false;
    }

    if (Array.isArray(items)) {
      return items
        .filter((item): item is JSONSchema7 => filterSchema(item))
        .some((item) => isExpandableProperty(item));
    }

    return isExpandableProperty(items);
  }

  if (anyOf) {
    return anyOf
      .filter((item): item is JSONSchema7 => filterSchema(item))
      .some((item) => isExpandableProperty(item));
  }

  return false;
}

function filterSchema(property: JSONSchema7Definition) {
  return property !== undefined && property !== true && property !== false;
}

function ExpandedRoot({
  property,
  defs,
}: {
  property: JSONSchema7Definition;
  defs: Record<string, JSONSchema7Definition> | undefined;
}) {
  if (property === true || property === false || !property) {
    return null;
  }

  const {properties, anyOf, $ref, type} = property;

  if (properties) {
    return (
      <div className={styles.expansion}>
        <SchemaRoot schema={property} defs={defs} />
      </div>
    );
  }

  if (type === 'array') {
    const items = Array.isArray(property.items)
      ? property.items
      : property.items
        ? [property.items]
        : [];

    return (
      <div className={styles.expansion}>
        {items
          .filter((item) => typeof item !== 'boolean' && typeof item !== 'undefined')
          .map((item, ii) => {
            return <ExpandedRoot key={ii} property={item} defs={defs} />;
          })}
      </div>
    );
  }

  if (anyOf) {
    return (
      <div className={styles.expansion}>
        {anyOf
          .filter((item) => typeof item !== 'boolean' && typeof item !== 'undefined')
          .map((item, ii) => {
            return <ExpandedRoot key={ii} property={item} defs={defs} />;
          })}
      </div>
    );
  }

  if ($ref) {
    const refName = $ref.split('/').pop();
    if (refName) {
      const definition = defs?.[refName];
      if (typeof definition !== 'boolean' && typeof definition !== 'undefined') {
        return (
          <div className={styles.expansion}>
            <SchemaRoot schema={definition} defs={defs} />
          </div>
        );
      }
    }
  }

  return null;
}

function propertyTypeToString(typeName: JSONSchema7TypeName) {
  switch (typeName) {
    case 'object':
      return 'object';
    case 'array':
      return 'array';
    case 'string':
      return 'string';
    case 'number':
      return 'number';
    case 'integer':
      return 'integer';
    case 'boolean':
      return 'boolean';
    case 'null':
      return 'null';
    default:
      return typeName;
  }
}

function PropertyRef({
  ref,
  defs,
}: {
  ref: string;
  defs: Record<string, JSONSchema7Definition> | undefined;
}) {
  const refName = ref.split('/').pop();
  if (refName) {
    const definition = defs?.[refName];
    if (definition) {
      return <PropertyType title={refName} property={definition} defs={defs} />;
    }
  }
  return null;
}

function PropertyType({
  title,
  property,
  defs,
}: {
  title?: string;
  property: JSONSchema7Definition;
  defs: Record<string, JSONSchema7Definition> | undefined;
}) {
  if (property === true || property === false) {
    return <TypeTag name={String(property)} />;
  }

  if (!property) {
    return null;
  }

  const type = property.type;
  if (Array.isArray(type)) {
    const items = Array.isArray(type) ? type : type === undefined ? [] : [type];
    return (
      <div>
        {items.map((item) => (
          <TypeTag key={item} name={propertyTypeToString(item)} />
        ))}
      </div>
    );
  }

  if (type === 'array') {
    return (
      <div>
        <ArrayTag items={property.items} defs={defs} />
      </div>
    );
  }

  const ref = property.$ref;
  if (ref) {
    const refName = ref.split('/').pop();
    if (refName) {
      const definition = defs?.[refName];
      if (definition !== undefined) {
        return <PropertyType title={refName} property={definition} defs={defs} />;
      }
    }
    return null;
  }

  if (title) {
    return <TypeTag name={title} />;
  }

  switch (type) {
    case 'object':
      return <TypeTag name={propertyTypeToString(type)} />;
    case 'string':
    case 'number':
    case 'boolean':
    case 'integer':
    case 'null':
      return <TypeTag name={propertyTypeToString(type)} />;
    default:
      return <div>none</div>;
  }
}

function PropertyAnyOf({
  anyOf,
  defs,
}: {
  anyOf: JSONSchema7['anyOf'];
  defs: Record<string, JSONSchema7Definition> | undefined;
}) {
  return (
    <div className={styles.anyOf}>
      <div className={styles.anyOfLabel}>Any of:</div>
      {(anyOf ?? []).map((definition, ii) => {
        return <PropertyType key={ii} property={definition} defs={defs} />;
      })}
    </div>
  );
}

const Chevron = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 20 20"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
    className={styles.chevron}
  >
    <path
      d="M6.175 7.15837L5 8.33337L10 13.3334L15 8.33337L13.825 7.15837L10 10.975L6.175 7.15837Z"
      fill="currentColor"
    />
  </svg>
);
