import {
  Box,
  Caption,
  Checkbox,
  Colors,
  FontFamily,
  Heading,
  TextInput,
} from '@dagster-io/ui-components';
import type {
  FieldTemplateProps,
  ObjectFieldTemplateProps,
  RegistryWidgetsType,
  WidgetProps,
} from '@rjsf/utils';
import type {CSSProperties, ChangeEvent} from 'react';
import {useState} from 'react';

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
  const {id, value, onChange, onBlur, placeholder, rawErrors} = props;
  const hasError = (rawErrors?.length ?? 0) > 0;
  return (
    <TextInput
      id={id}
      value={value ?? ''}
      onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e.target.value || undefined)}
      onBlur={(e) => onBlur(id, e.target.value)}
      placeholder={placeholder}
      strokeColor={hasError ? Colors.accentRed() : undefined}
      fill
    />
  );
}

function TextareaWidget(props: WidgetProps) {
  const {id, value, onChange, onBlur, placeholder, rawErrors} = props;
  const [focused, setFocused] = useState(false);
  const hasError = (rawErrors?.length ?? 0) > 0;
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
  const {id, value, options, onChange, onBlur, rawErrors, placeholder} = props;
  const enumOptions = options.enumOptions ?? [];
  const hasError = (rawErrors?.length ?? 0) > 0;
  return (
    <select
      id={id}
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value || undefined)}
      onBlur={(e) => onBlur(id, e.target.value)}
      style={nativeSelectStyle({hasError})}
    >
      <option value="">{placeholder ?? 'Select…'}</option>
      {enumOptions.map((opt) => (
        <option key={String(opt.value)} value={String(opt.value)}>
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
 * wrapping. Object groups render as plain stacked rows — labels live on the
 * parent FieldTemplate (e.g. "Target"), and the selected variant of an
 * ``anyOf``/``oneOf`` is already named by the dropdown, so a repeated group
 * title would just be noise.
 */
export function ObjectFieldTemplate(props: ObjectFieldTemplateProps) {
  const {properties} = props;
  const visibleProps = properties.filter((p) => !p.hidden);
  return (
    <Box flex={{direction: 'column', gap: 12}}>
      {visibleProps.map((p) => (
        <div key={p.name}>{p.content}</div>
      ))}
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
    errors,
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

  // RJSF passes displayLabel=false for top-level "root" wrappers, booleans,
  // and a few other cases — let those render unwrapped so we don't get nested
  // labels or duplicate spacing.
  if (!displayLabel || !label || schema.type === 'object' || schema.type === 'array') {
    return (
      <div className={classNames} style={style} id={id}>
        {children}
        {errors}
      </div>
    );
  }

  const hasError = (rawErrors?.length ?? 0) > 0;

  return (
    <Box flex={{direction: 'column', gap: 4}} className={classNames} style={style}>
      <Heading size={14} weight={600}>
        {label}
        {required ? <span style={{color: Colors.accentRed(), marginLeft: 2}}>*</span> : null}
      </Heading>
      {children}
      {schema.description ? (
        <Caption color={Colors.textLighter()}>{schema.description}</Caption>
      ) : null}
      {hasError && rawErrors ? (
        <Caption color={Colors.accentRed()}>{rawErrors.join(', ')}</Caption>
      ) : null}
    </Box>
  );
}
