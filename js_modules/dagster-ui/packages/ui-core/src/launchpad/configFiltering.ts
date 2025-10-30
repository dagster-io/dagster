import * as yaml from 'yaml';

import {LaunchpadRootQuery} from './types/LaunchpadAllowedRoot.types';

export const filterDefaultYamlForSubselection = (
  defaultYaml: string,
  opNames: Set<string>,
): string => {
  const parsedYaml = yaml.parse(defaultYaml);

  const opsConfig = parsedYaml['ops'];
  if (opsConfig) {
    const filteredOpKeys = Object.keys(opsConfig).filter((entry) => {
      return opNames.has(entry);
    });
    const filteredOpsConfig = Object.fromEntries(
      filteredOpKeys.map((key) => [key, opsConfig[key]]),
    );
    parsedYaml['ops'] = filteredOpsConfig;
  }

  return yaml.stringify(parsedYaml);
};

export const filterDefaultYamlOptionalResources = (
  defaultYaml: string,
  runConfigSchema: LaunchpadRootQuery['runConfigSchemaOrError'],
): string => {
  if (!runConfigSchema || runConfigSchema.__typename !== 'RunConfigSchema') {
    return defaultYaml;
  }

  const parsedYaml = yaml.parse(defaultYaml);

  // Find the root config type to get the structure
  const rootConfigType = runConfigSchema.allConfigTypes.find(
    (type) => type.key === runConfigSchema.rootConfigType.key,
  );
  if (!rootConfigType || rootConfigType.__typename !== 'CompositeConfigType') {
    return defaultYaml;
  }

  const resourcesField = rootConfigType.fields.find((field) => field.name === 'resources');
  if (!resourcesField || !parsedYaml.resources) {
    return defaultYaml;
  }
  const resourcesConfigType = runConfigSchema.allConfigTypes.find(
    (type) => type.key === resourcesField.configTypeKey,
  );

  if (!resourcesConfigType || resourcesConfigType.__typename !== 'CompositeConfigType') {
    return defaultYaml;
  }
  const optionalResources = resourcesConfigType.fields
    .filter((field) => !field.isRequired)
    .map((field) => field.name);

  for (const resourceKey of optionalResources) {
    delete parsedYaml.resources[resourceKey];
  }
  if (Object.keys(parsedYaml.resources).length === 0) {
    delete parsedYaml.resources;
  }

  return yaml.stringify(parsedYaml);
};
