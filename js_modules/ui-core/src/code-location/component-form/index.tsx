import Form from '@rjsf/core';
import type {IChangeEvent} from '@rjsf/core';
import type {RJSFSchema, UiSchema} from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import {useCallback, useMemo, useState} from 'react';

import {isFormDataValid} from './validate';
import {
  ArrayFieldTemplate,
  FieldTemplate,
  ObjectFieldTemplate,
  WrapIfAdditionalTemplate,
  widgets,
} from './widgets';
import type {ComponentFormContext} from './widgets';

interface Props {
  dataSchema: RJSFSchema;
  uiSchema: UiSchema;
  formData: Record<string, any>;
  onChange: (next: Record<string, any>, isValid: boolean) => void;
}

/**
 * Thin wrapper around react-jsonschema-form. The Dagster-emitted JSON schema is
 * split into the (dataSchema, uiSchema) pair RJSF expects server-side (see
 * ``dagster.components.resolved.form_schema.split_form_schema``); this renders
 * that pair with our Blueprint-themed widgets and field template.
 */
export function ComponentSchemaForm({dataSchema, uiSchema, formData, onChange}: Props) {
  // Ids of fields the user has visited (widgets mark on blur). Validation
  // errors are displayed only for touched fields so a freshly opened form
  // isn't a wall of red; submit-enablement is computed independently below.
  const [touched, setTouched] = useState<ReadonlySet<string>>(() => new Set());
  const markTouched = useCallback((id: string) => {
    setTouched((prev) => {
      if (prev.has(id)) {
        return prev;
      }
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  }, []);
  const formContext: ComponentFormContext = useMemo(
    () => ({
      isTouched: (id: string) => touched.has(id),
      markTouched,
    }),
    [touched, markTouched],
  );

  return (
    <Form
      schema={dataSchema}
      uiSchema={uiSchema}
      formData={formData}
      validator={validator}
      widgets={widgets}
      templates={{ArrayFieldTemplate, FieldTemplate, ObjectFieldTemplate, WrapIfAdditionalTemplate}}
      formContext={formContext}
      liveValidate
      showErrorList={false}
      // Avoid colliding with the page's #root selector (sets width: 100vw on
      // the app shell), which RJSF would otherwise apply to its own root
      // form-group via the default idPrefix of "root".
      idPrefix="cf"
      // The bundled ``@rjsf/validator-ajv8`` JIT-compiles schemas with eval,
      // which the production CSP rejects (``unsafe-eval`` is intentionally
      // disallowed). Ajv keeps running for UX touches (highlighting, etc.) but
      // its ``errors`` list is dominated by the CSP exception and unusable for
      // submit-enablement. Decide validity ourselves with a lightweight
      // required-field walker instead. See ``./validate.ts``.
      onChange={({formData: next}: IChangeEvent) =>
        onChange(next ?? {}, isFormDataValid(dataSchema, next))
      }
    >
      {/* Suppress the default submit button — submission is owned by parent dialog */}
      <span style={{display: 'none'}} />
    </Form>
  );
}
