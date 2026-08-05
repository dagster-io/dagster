import {
  Box,
  Button,
  Checkbox,
  CollapsibleSection,
  Colors,
  FontFamily,
  Heading,
  Icon,
  Text,
  TextInput,
} from '@dagster-io/ui-components';
import type {
  ArrayFieldTemplateProps,
  FieldTemplateProps,
  ObjectFieldTemplateProps,
  RegistryWidgetsType,
  WidgetProps,
  WrapIfAdditionalTemplateProps,
} from '@rjsf/utils';
import {
  ADDITIONAL_PROPERTY_FLAG,
  canExpand,
  enumOptionsIndexForValue,
  enumOptionsValueForIndex,
} from '@rjsf/utils';
import type {CSSProperties, ChangeEvent} from 'react';
import {useState} from 'react';

/**
 * Shared via RJSF's ``formContext``. Validation errors are only *displayed*
 * for fields the user has visited (blur marks a field touched) — a pristine
 * form full of red "required" errors helps no one. Submit-enablement is
 * decided independently in ``validate.ts``, so hiding errors here never lets
 * an invalid form through.
 */
export interface ComponentFormContext {
  isTouched: (id: string) => boolean;
  markTouched: (id: string) => void;
}

function getFormContext(props: WidgetProps | FieldTemplateProps): ComponentFormContext | undefined {
  return props.registry?.formContext as ComponentFormContext | undefined;
}

function showErrors(props: WidgetProps | FieldTemplateProps): boolean {
  const ctx = getFormContext(props);
  const hasError = ((props.rawErrors as string[] | undefined)?.length ?? 0) > 0;
  return hasError && (ctx?.isTouched(props.id) ?? true);
}

function chevronSvg(stroke: string): string {
  const encoded = encodeURIComponent(stroke);
  return `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='${encoded}' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`;
}

function nativeSelectStyle({hasError = false}: {hasError?: boolean} = {}): CSSProperties {
  return {
    padding: '6px 32px 6px 12px',
    borderRadius: 8,
    border: `1px solid ${hasError ? Colors.accentRed() : Colors.borderDefault()}`,
    background: Colors.backgroundDefault(),
    color: Colors.textDefault(),
    fontSize: 13,
    cursor: 'pointer',
    outline: 'none',
    appearance: 'none',
    backgroundImage: chevronSvg(Colors.textLight()),
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 10px center',
    width: '100%',
    boxSizing: 'border-box',
  };
}

function TextWidget(props: WidgetProps) {
  const {id, value, onChange, onBlur, placeholder, schema} = props;
  const ctx = getFormContext(props);
  const hasError = showErrors(props);
  const isNumeric = schema.type === 'number' || schema.type === 'integer';
  const parse = (raw: string): string | number | undefined => {
    if (raw === '') {
      return undefined;
    }
    if (!isNumeric) {
      return raw;
    }
    const n = Number(raw);
    return Number.isFinite(n) ? n : raw;
  };
  return (
    <TextInput
      id={id}
      type={isNumeric ? 'number' : 'text'}
      value={value ?? ''}
      onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(parse(e.target.value))}
      onBlur={(e) => {
        ctx?.markTouched(id);
        onBlur(id, parse(e.target.value));
      }}
      placeholder={placeholder}
      strokeColor={hasError ? Colors.accentRed() : undefined}
      fill
    />
  );
}

function TextareaWidget(props: WidgetProps) {
  const {id, value, onChange, onBlur, placeholder} = props;
  const ctx = getFormContext(props);
  const [focused, setFocused] = useState(false);
  const hasError = showErrors(props);
  let borderColor = Colors.borderDefault();
  if (hasError) {
    borderColor = Colors.accentRed();
  } else if (focused) {
    borderColor = Colors.accentBlue();
  }
  return (
    <textarea
      id={id}
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value || undefined)}
      onFocus={() => setFocused(true)}
      onBlur={(e) => {
        setFocused(false);
        ctx?.markTouched(id);
        onBlur(id, e.target.value);
      }}
      placeholder={placeholder}
      rows={4}
      style={{
        padding: '8px 12px',
        borderRadius: 8,
        border: `1px solid ${borderColor}`,
        boxShadow: focused && !hasError ? `0 0 0 1px ${Colors.accentBlue()}` : 'none',
        background: Colors.backgroundDefault(),
        color: Colors.textDefault(),
        fontSize: 13,
        fontFamily: FontFamily.monospace,
        resize: 'vertical',
        width: '100%',
        minHeight: 80,
        boxSizing: 'border-box',
        outline: 'none',
        lineHeight: '1.5',
        transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
      }}
    />
  );
}

function CheckboxWidget(props: WidgetProps) {
  const {id, value, onChange, label} = props;
  return (
    <Checkbox
      id={id}
      checked={!!value}
      onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e.target.checked)}
      label={label}
    />
  );
}

function SelectWidget(props: WidgetProps) {
  const {id, value, options, onChange, onBlur, placeholder} = props;
  const ctx = getFormContext(props);
  const enumOptions = options.enumOptions ?? [];
  const {emptyValue} = options;
  const hasError = showErrors(props);
  // Options are keyed by index (not stringified value) so non-string enum
  // values — numeric/boolean ``Literal``/``Enum`` — round-trip with their
  // original type instead of being coerced to strings on submit.
  const selectedIndex = enumOptionsIndexForValue(value, enumOptions, false);
  return (
    <select
      id={id}
      value={typeof selectedIndex === 'string' ? selectedIndex : ''}
      onChange={(e) => onChange(enumOptionsValueForIndex(e.target.value, enumOptions, emptyValue))}
      onBlur={(e) => {
        ctx?.markTouched(id);
        onBlur(id, enumOptionsValueForIndex(e.target.value, enumOptions, emptyValue));
      }}
      style={nativeSelectStyle({hasError})}
    >
      <option value="">{placeholder ?? 'Select…'}</option>
      {enumOptions.map((opt, index) => (
        <option key={index} value={String(index)}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export const widgets: RegistryWidgetsType = {
  TextWidget,
  TextareaWidget,
  CheckboxWidget,
  SelectWidget,
};

/**
 * Custom ObjectFieldTemplate that drops RJSF's default ``<fieldset><legend>``
 * wrapping and renders object properties as plain stacked rows. Fields whose
 * uiSchema carries ``ui:advanced`` (from ``ComponentFormConfig(advanced=True)``)
 * are tucked into a collapsed "Advanced" section at the bottom.
 */
export function ObjectFieldTemplate(props: ObjectFieldTemplateProps) {
  const {properties, uiSchema, schema, formData, onAddClick, disabled, readonly} = props;
  const visibleProps = properties.filter((p) => !p.hidden);
  const isAdvanced = (name: string) =>
    (uiSchema as Record<string, any> | undefined)?.[name]?.['ui:advanced'] === true;
  const mainProps = visibleProps.filter((p) => !isAdvanced(p.name));
  const advancedProps = visibleProps.filter((p) => isAdvanced(p.name));
  return (
    <Box flex={{direction: 'column', gap: 12}}>
      {mainProps.map((p) => (
        <div key={p.name}>{p.content}</div>
      ))}
      {canExpand(schema, uiSchema, formData) ? (
        <Box flex={{direction: 'row'}}>
          <Button
            type="button"
            icon={<Icon name="add_circle" />}
            onClick={onAddClick(schema)}
            disabled={disabled || readonly}
          >
            Add entry
          </Button>
        </Box>
      ) : null}
      {advancedProps.length > 0 ? (
        <Box border="top" padding={{top: 8}} margin={{top: 4}}>
          <CollapsibleSection
            isInitiallyCollapsed
            header={
              <Text size={12} color="textLight">
                Advanced ({advancedProps.length})
              </Text>
            }
            headerWrapperProps={{style: {cursor: 'pointer'}}}
          >
            <Box flex={{direction: 'column', gap: 12}} padding={{top: 12, left: 20}}>
              {advancedProps.map((p) => (
                <div key={p.name}>{p.content}</div>
              ))}
            </Box>
          </CollapsibleSection>
        </Box>
      ) : null}
    </Box>
  );
}

/**
 * Custom ArrayFieldTemplate replacing RJSF's default fieldset/legend markup:
 * each item renders in a bordered card with an index header and a remove
 * button, followed by a themed "Add item" button.
 */
export function ArrayFieldTemplate(props: ArrayFieldTemplateProps) {
  const {items, canAdd, onAddClick, disabled, readonly} = props;
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      {items.map((item) => (
        <Box
          key={item.key}
          border="all"
          padding={{vertical: 8, horizontal: 12}}
          style={{borderRadius: 8}}
          flex={{direction: 'column', gap: 8}}
        >
          <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
            <Text size={12} color="textLighter">
              {item.index + 1}
            </Text>
            {item.hasRemove ? (
              <Button
                type="button"
                icon={<Icon name="delete" />}
                onClick={item.onDropIndexClick(item.index)}
                disabled={disabled || readonly}
              />
            ) : null}
          </Box>
          {item.children}
        </Box>
      ))}
      {canAdd ? (
        <Box flex={{direction: 'row'}}>
          <Button
            type="button"
            icon={<Icon name="add_circle" />}
            onClick={onAddClick}
            disabled={disabled || readonly}
          >
            Add item
          </Button>
        </Box>
      ) : null}
    </Box>
  );
}

// Ajv's messages are developer-speak ("must have required property 'Name'");
// translate the common cases into something a form user expects.
function friendlyError(message: string): string {
  if (/required property/.test(message)) {
    return 'This field is required.';
  }
  return message;
}

/**
 * Renders dict-style entries (``additionalProperties``) as a key input / value
 * input / remove-button row. Non-additional fields pass through untouched.
 * The key commits on blur so editing it doesn't re-key (and remount) the
 * form-data entry on every keystroke.
 */
export function WrapIfAdditionalTemplate(props: WrapIfAdditionalTemplateProps) {
  const {
    id,
    classNames,
    style,
    disabled,
    label,
    onKeyChange,
    onDropPropertyClick,
    readonly,
    schema,
    children,
  } = props;
  const isAdditional = ADDITIONAL_PROPERTY_FLAG in schema;
  if (!isAdditional) {
    return (
      <div className={classNames} style={style}>
        {children}
      </div>
    );
  }
  return (
    <Box
      flex={{direction: 'row', gap: 8, alignItems: 'center'}}
      className={classNames}
      style={style}
    >
      <div style={{flex: 1}}>
        <TextInput
          id={`${id}-key`}
          defaultValue={label}
          onBlur={(e) => onKeyChange(e.target.value)}
          placeholder="Key"
          disabled={disabled || readonly}
          fill
        />
      </div>
      <div style={{flex: 1}}>{children}</div>
      <Button
        type="button"
        icon={<Icon name="delete" />}
        onClick={onDropPropertyClick(label)}
        disabled={disabled || readonly}
      />
    </Box>
  );
}

export function FieldTemplate(props: FieldTemplateProps) {
  const {
    id,
    classNames,
    style,
    label,
    children,
    rawErrors,
    hidden,
    required,
    displayLabel,
    schema,
    uiSchema,
  } = props;

  // Hide:
  //   1. ``hidden`` set explicitly on the field.
  //   2. ``ui:widget: 'hidden'`` from uiSchema — RJSF still calls FieldTemplate
  //      and would otherwise leak label/description chrome.
  //   3. ``const``-valued schemas (discriminator literals for tagged unions):
  //      the value is forced by the schema and the user has no choice to make.
  //      Pydantic re-fills these from defaults when YAML lacks the key, and
  //      RJSF's getDefaultFormState seeds the const into formData on mount.
  const isConst = schema?.const !== undefined;
  if (hidden || uiSchema?.['ui:widget'] === 'hidden' || isConst) {
    return <div style={{display: 'none'}}>{children}</div>;
  }

  // Decide whether this field carries its own heading. RJSF passes
  // ``displayLabel: false`` (and often no ``label``) for objects, arrays, and
  // booleans; booleans render their label inside the checkbox and structured
  // objects label their own children, but arrays and dict-style objects
  // (additionalProperties) would otherwise render with no visible name at all.
  const headingText = label || (typeof schema.title === 'string' ? schema.title : '');
  const isRoot = id === 'cf';
  const isAdditional = ADDITIONAL_PROPERTY_FLAG in schema;
  // RJSF materializes (possibly empty) ``properties`` for additionalProperties
  // objects, so key off ``additionalProperties`` itself.
  const isDictLike = schema.type === 'object' && Boolean(schema.additionalProperties);
  const isArray = schema.type === 'array';
  const isBoolean = schema.type === 'boolean';
  const showHeading =
    !isRoot &&
    !isBoolean &&
    !isAdditional &&
    !!headingText &&
    (displayLabel || isArray || isDictLike);

  const {WrapIfAdditionalTemplate: WrapTemplate} = props.registry.templates;

  if (!showHeading) {
    return (
      <WrapTemplate {...props}>
        <div className={classNames} style={style} id={id}>
          {children}
        </div>
      </WrapTemplate>
    );
  }

  const hasError = showErrors(props);

  return (
    <WrapTemplate {...props}>
      <Box flex={{direction: 'column', gap: 4}} className={classNames} style={style}>
        <Heading size={14} weight={600}>
          {headingText}
          {required ? <span style={{color: Colors.accentRed(), marginLeft: 2}}>*</span> : null}
        </Heading>
        {children}
        {schema.description ? (
          <Text size={12} color="textLighter">
            {schema.description}
          </Text>
        ) : null}
        {hasError && rawErrors ? (
          <Text size={12} color="accentRed">
            {[...new Set(rawErrors.map(friendlyError))].join(' ')}
          </Text>
        ) : null}
      </Box>
    </WrapTemplate>
  );
}
