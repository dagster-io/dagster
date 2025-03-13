'use client';

import {JSONSchema7, JSONSchema7Definition, JSONSchema7TypeName} from 'json-schema';

import styles from './css/ComponentSchema.module.css';
import TypeTag from '@/app/components/schema/TypeTag';
import {useState} from 'react';
import clsx from 'clsx';
import ArrayTag from '@/app/components/schema/ArrayTag';

type ExtendedJSONSchema7Definition = JSONSchema7Definition & {
  dagster_required_scope?: Record<string, string>;
};

interface Props {
  schema: string;
  name: string;
}

export default function ComponentSchema({schema, name}: Props) {
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
  const title = jsonSchema.title;
  const defs = jsonSchema.$defs;

  console.log(jsonSchema);

  return (
    <Root
      title={undefined}
      properties={{type: {type: 'string', default: name}, attributes: jsonSchema}}
      defs={defs}
      startExpanded
    />
  );
}

function Root({
  title,
  properties,
  defs,
  startExpanded,
}: {
  title: string | undefined;
  properties: Record<string, ExtendedJSONSchema7Definition>;
  defs: Record<string, ExtendedJSONSchema7Definition> | undefined;
  startExpanded?: boolean;
}) {
  return (
    <div className={styles.schemaContainer}>
      {title ? <div className={styles.schemaTitle}>{title}</div> : null}
      {Object.entries(properties).map(([key, property]) => (
        <Property
          key={key}
          name={key}
          property={property}
          defs={defs}
          startExpanded={startExpanded}
        />
      ))}
    </div>
  );
}

function Property({
  name,
  property,
  defs,
  startExpanded,
}: {
  name: string;
  property: ExtendedJSONSchema7Definition;
  defs: Record<string, ExtendedJSONSchema7Definition> | undefined;
  startExpanded?: boolean;
}) {
  const [expanded, setExpanded] = useState(startExpanded ?? false);

  const onToggleExpansion = () => {
    setExpanded((current) => !current);
  };

  if (property === true || property === false) {
    return null;
  }

  const {
    anyOf,
    type,
    description,
    default: defaultValue,
    $ref,
    required,
    examples,
    dagster_required_scope: scope,
  } = property;

  const expandable =
    !!$ref ||
    type === 'object' ||
    (type === 'array' &&
      property.items &&
      Object.values(property.items).some((item) => typeof item !== 'boolean' && !!item.$ref)) ||
    !!(
      anyOf &&
      anyOf.some(
        (item) =>
          typeof item !== 'boolean' &&
          (item.type === 'object' || item.type === 'array' || !!item.$ref),
      )
    );

  const firstExample = examples ? (Array.isArray(examples) ? examples[0] : examples) : null;

  const onClick = () => {
    console.log(name, property);
  };

  return (
    <div className={styles.propertyRoot}>
      <button
        disabled={!expandable}
        className={clsx(styles.expandButton, expanded && styles.expanded)}
        onClick={onToggleExpansion}
      >
        <Chevron />
      </button>
      <div className={styles.propertyContainer}>
        <div className={styles.property}>
          <div className={styles.propertyNameAndTypes}>
            <div className={styles.propertyName}>{name}</div>
            {$ref ? <PropertyRef ref={$ref} defs={defs} onClick={onClick} /> : null}
            {type ? <PropertyType property={property} defs={defs} onClick={onClick} /> : null}
            {anyOf ? <PropertyAnyOf anyOf={anyOf} defs={defs} onClick={onClick} /> : null}
          </div>
          {required ? <div className={styles.required}>required</div> : null}
        </div>
        {description || defaultValue || examples || scope ? (
          <div className={styles.propertyDescriptionContainer}>
            <div className={styles.propertyDescription}>{description}</div>
            {scope ? (
              <div className={styles.propertyScopes}>
                <div className={styles.schemaTitle}>Scopes</div>
                {Object.entries(scope).map(([key, value]) => (
                  <div className={styles.propertyScope} key={key}>
                    <div className={styles.propertyNameAndTypes}>
                      <div className={styles.propertyName}>{key}</div>
                      <TypeTag name={value.scope_type} onClick={onClick} />
                    </div>
                    <div className={styles.propertyDescriptionContainer}>
                      <div className={styles.propertyDescription}>{value.description}</div>
                      {value.scope_parameters ? (
                        <div className={styles.scopeFnParameters}>
                          Parameters:{' '}
                          {Object.entries(value.scope_parameters).map(([key, value]) => (
                            <div key={key} className={styles.scopeFnParameter}>
                              <div className={styles.propertyNameAndTypes}>
                                {key} <TypeTag name={value.type} onClick={onClick} />
                              </div>
                              <div className={styles.propertyDefaultValue}>{value.default}</div>
                            </div>
                          ))}
                        </div>
                      ) : null}
                      {value.scope_return_type ? (
                        <div className={styles.scopeFnReturnType}>
                          Return value:
                          <TypeTag name={value.scope_return_type} onClick={onClick} />
                        </div>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
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
        {expanded ? <ExpandedRoot property={property} defs={defs} /> : null}
      </div>
    </div>
  );
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

  const {properties, anyOf, $ref, title} = property;

  if (properties) {
    return (
      <div className={styles.expansion}>
        <Root title={title} properties={properties} defs={defs} />
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
            <Root title={refName} properties={definition.properties ?? {}} defs={defs} />
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
  onClick,
}: {
  ref: string;
  defs: Record<string, JSONSchema7Definition> | undefined;
  onClick: () => void;
}) {
  const refName = ref.split('/').pop();
  if (refName) {
    const definition = defs?.[refName];
    if (definition) {
      return <PropertyType title={refName} property={definition} defs={defs} onClick={onClick} />;
    }
  }
  return null;
}

function PropertyType({
  title,
  property,
  defs,
  onClick,
}: {
  title?: string;
  property: JSONSchema7Definition;
  defs: Record<string, JSONSchema7Definition> | undefined;
  onClick: () => void;
}) {
  if (property === true || property === false) {
    return <TypeTag name={String(property)} onClick={onClick} />;
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
          <TypeTag key={item} name={propertyTypeToString(item)} onClick={onClick} />
        ))}
      </div>
    );
  }

  if (type === 'array') {
    return (
      <div>
        <ArrayTag items={property.items} defs={defs} onClick={onClick} />
      </div>
    );
  }

  const ref = property.$ref;
  if (ref) {
    const refName = ref.split('/').pop();
    if (refName) {
      const definition = defs?.[refName];
      if (definition !== undefined) {
        return <PropertyType title={refName} property={definition} defs={defs} onClick={onClick} />;
      }
    }
    return null;
  }

  if (title) {
    return <TypeTag name={title} onClick={onClick} />;
  }

  switch (type) {
    case 'object':
      return <TypeTag name={propertyTypeToString(type)} onClick={onClick} />;
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
  onClick,
}: {
  anyOf: JSONSchema7['anyOf'];
  defs: Record<string, JSONSchema7Definition> | undefined;
  onClick: () => void;
}) {
  return (
    <div className={styles.anyOf}>
      <div>Any of:</div>
      {(anyOf ?? []).map((definition, ii) => {
        return <PropertyType key={ii} property={definition} defs={defs} onClick={onClick} />;
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
