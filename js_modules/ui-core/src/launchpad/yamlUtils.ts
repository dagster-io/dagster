import merge from 'deepmerge';
import * as yaml from 'yaml';

export const sanitizeConfigYamlString = (yamlString: string) => (yamlString || '').trim() || '{}';

/**
 * Utility function to merge two YAML documents:
 * - Stringify string values with quotes. Avoids known issues with "5:30" becoming 5:30 which parses as a Sexagesimal number
 * - When merging arrays, combine rather than concatenate (the default deepmerge behavior)
 * -
 */
export function mergeYaml(
  base: string | Record<string, any>,
  overrides: string | Record<string, any>,
  extraOpts?: yaml.SchemaOptions,
) {
  const baseObj = typeof base === 'string' ? yaml.parse(sanitizeConfigYamlString(base)) : base;

  const overridesObj =
    typeof overrides === 'string' ? yaml.parse(sanitizeConfigYamlString(overrides)) : overrides;

  const arrayCombineMerge: merge.Options['arrayMerge'] = (target, source, options) => {
    const destination = target.slice();

    source.forEach((item, index) => {
      if (typeof destination[index] === 'undefined') {
        destination[index] = options?.cloneUnlessOtherwiseSpecified(item, options);
      } else if (options?.isMergeableObject(item)) {
        destination[index] = merge(target[index], item, options);
      } else if (target.indexOf(item) === -1) {
        destination.push(item);
      }
    });
    return destination;
  };

  const mergedObj = merge(baseObj, overridesObj, {
    arrayMerge: arrayCombineMerge,
  });

  return yaml.stringify(mergedObj, {
    defaultKeyType: 'PLAIN',
    defaultStringType: 'QUOTE_SINGLE',
    ...extraOpts,
  });
}
