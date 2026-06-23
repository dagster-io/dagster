/**
 * Lightweight required-field validator for the App Managed component form.
 *
 * Why not use RJSF's bundled Ajv validator? The webserver's CSP forbids
 * ``unsafe-eval``, but Ajv 8 JIT-compiles every schema with ``new Function()``
 * — every validation call throws a CSP violation and ``errors`` is never
 * empty, so the "Add component" button can never enable.
 *
 * This pass covers what the form actually needs for submit-enablement: each
 * required field has a non-empty value, recursing into objects and picking the
 * first matching variant for ``anyOf``/``oneOf``. It is intentionally narrow
 * — deeper structural validation happens on the Python side when the YAML is
 * loaded.
 */

type AnyObj = Record<string, unknown>;

function isObject(v: unknown): v is AnyObj {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

function isMissing(v: unknown): boolean {
  if (v === undefined || v === null) {
    return true;
  }
  if (typeof v === 'string' && v.trim() === '') {
    return true;
  }
  return false;
}

function resolveRef(node: AnyObj, root: AnyObj): AnyObj {
  const ref = node.$ref;
  if (typeof ref !== 'string' || !ref.startsWith('#/')) {
    return node;
  }
  let current: unknown = root;
  for (const segment of ref.slice(2).split('/')) {
    if (!isObject(current)) {
      return node;
    }
    current = current[segment];
  }
  return isObject(current) ? current : node;
}

function checkSchema(schemaNode: unknown, data: unknown, root: AnyObj): boolean {
  if (!isObject(schemaNode)) {
    return true;
  }
  const node = resolveRef(schemaNode, root);

  // ``anyOf``/``oneOf``: at least one variant must validate against the data.
  for (const key of ['anyOf', 'oneOf'] as const) {
    const variants = node[key];
    if (Array.isArray(variants) && variants.length > 0) {
      return variants.some((v) => checkSchema(v, data, root));
    }
  }

  // Required-field check only applies to objects.
  const required = node.required;
  const properties = node.properties;
  if (Array.isArray(required) && isObject(properties)) {
    if (!isObject(data)) {
      return false;
    }
    for (const name of required) {
      if (typeof name !== 'string') {
        continue;
      }
      const childData = data[name];
      if (isMissing(childData)) {
        return false;
      }
      const childSchema = properties[name];
      if (!checkSchema(childSchema, childData, root)) {
        return false;
      }
    }
  }
  return true;
}

export function isFormDataValid(schema: unknown, formData: unknown): boolean {
  if (!isObject(schema)) {
    return true;
  }
  return checkSchema(schema, formData, schema);
}
