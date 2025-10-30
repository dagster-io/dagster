import {
  buildCompositeConfigType,
  buildConfigTypeField,
  buildPipelineNotFoundError,
  buildRunConfigSchema,
} from '../../graphql/types';
import {
  filterDefaultYamlForSubselection,
  filterDefaultYamlOptionalResources,
} from '../configFiltering';
import {LaunchpadRootQuery} from '../types/LaunchpadAllowedRoot.types';

describe('filterDefaultYamlForSubselection', () => {
  it('filters ops config based on provided op names', () => {
    const yamlInput = `
ops:
  op1:
    config:
      value: 1
  op2:
    config:
      value: 2
  op3:
    config:
      value: 3
resources:
  db: {}
`;

    const opNames = new Set(['op1', 'op3']);
    const result = filterDefaultYamlForSubselection(yamlInput, opNames);

    expect(result).toContain('op1');
    expect(result).toContain('op3');
    expect(result).not.toContain('op2');
    expect(result).toContain('resources');
    expect(result).toContain('db');
  });

  it('handles empty op names set', () => {
    const yamlInput = `
ops:
  op1:
    config:
      value: 1
  op2:
    config:
      value: 2
`;

    const opNames = new Set<string>();
    const result = filterDefaultYamlForSubselection(yamlInput, opNames);

    expect(result).toContain('ops: {}');
  });

  it('handles yaml without ops section', () => {
    const yamlInput = `
resources:
  db: {}
execution:
  multiprocess: {}
`;

    const opNames = new Set(['op1']);
    const result = filterDefaultYamlForSubselection(yamlInput, opNames);

    expect(result).toContain('resources');
    expect(result).toContain('execution');
    expect(result).not.toContain('ops');
  });

  it('handles empty yaml', () => {
    const yamlInput = '{}';
    const opNames = new Set(['op1']);
    const result = filterDefaultYamlForSubselection(yamlInput, opNames);

    expect(result.trim()).toBe('{}');
  });
});

describe('filterDefaultYamlOptionalResources', () => {
  const createMockRunConfigSchema = (
    resourceFields: Array<{name: string; isRequired: boolean}>,
  ): LaunchpadRootQuery['runConfigSchemaOrError'] =>
    buildRunConfigSchema({
      rootDefaultYaml: '',
      rootConfigType: buildCompositeConfigType({
        key: 'root-key',
      }),
      allConfigTypes: [
        buildCompositeConfigType({
          key: 'root-key',
          description: null,
          isSelector: false,
          typeParamKeys: [],
          fields: [
            buildConfigTypeField({
              name: 'resources',
              description: null,
              isRequired: false,
              configTypeKey: 'resources-key',
              defaultValueAsJson: null,
            }),
          ],
        }),
        buildCompositeConfigType({
          key: 'resources-key',
          description: null,
          isSelector: false,
          typeParamKeys: [],
          fields: resourceFields.map((field) =>
            buildConfigTypeField({
              name: field.name,
              description: null,
              isRequired: field.isRequired,
              configTypeKey: 'String',
              defaultValueAsJson: null,
            }),
          ),
        }),
      ],
    });

  it('removes optional resources and keeps required ones', () => {
    const yamlInput = `
resources:
  required_db:
    host: localhost
  optional_cache:
    ttl: 300
  another_optional:
    setting: value
ops:
  my_op: {}
`;

    const schema = createMockRunConfigSchema([
      {name: 'required_db', isRequired: true},
      {name: 'optional_cache', isRequired: false},
      {name: 'another_optional', isRequired: false},
    ]);

    const result = filterDefaultYamlOptionalResources(yamlInput, schema);

    expect(result).toContain('required_db');
    expect(result).not.toContain('optional_cache');
    expect(result).not.toContain('another_optional');
    expect(result).toContain('ops');
  });

  it('removes entire resources section when no required resources exist', () => {
    const yamlInput = `
resources:
  optional_cache:
    ttl: 300
  another_optional:
    setting: value
ops:
  my_op: {}
`;

    const schema = createMockRunConfigSchema([
      {name: 'optional_cache', isRequired: false},
      {name: 'another_optional', isRequired: false},
    ]);

    const result = filterDefaultYamlOptionalResources(yamlInput, schema);

    expect(result).not.toContain('resources');
    expect(result).not.toContain('optional_cache');
    expect(result).not.toContain('another_optional');
    expect(result).toContain('ops');
  });

  it('handles yaml without resources section', () => {
    const yamlInput = `
ops:
  my_op: {}
execution:
  multiprocess: {}
`;

    const schema = createMockRunConfigSchema([{name: 'some_resource', isRequired: false}]);

    const result = filterDefaultYamlOptionalResources(yamlInput, schema);

    expect(result).toBe(yamlInput);
  });

  it('returns original yaml when schema is invalid', () => {
    const yamlInput = `
resources:
  some_resource: {}
`;

    const invalidSchema: LaunchpadRootQuery['runConfigSchemaOrError'] = buildPipelineNotFoundError({
      message: 'Pipeline not found',
    });

    const result = filterDefaultYamlOptionalResources(yamlInput, invalidSchema);

    expect(result).toBe(yamlInput);
  });

  it('returns original yaml when root config type is not found', () => {
    const yamlInput = `
resources:
  some_resource: {}
`;

    const schema: LaunchpadRootQuery['runConfigSchemaOrError'] = buildRunConfigSchema({
      rootDefaultYaml: '',
      rootConfigType: buildCompositeConfigType({
        key: 'root-key',
      }),
      allConfigTypes: [
        // Empty array - root config type not found
      ],
    });

    const result = filterDefaultYamlOptionalResources(yamlInput, schema);

    expect(result).toBe(yamlInput);
  });

  it('returns original yaml when resources field is not found in root config', () => {
    const yamlInput = `
resources:
  some_resource: {}
`;

    const schema: LaunchpadRootQuery['runConfigSchemaOrError'] = buildRunConfigSchema({
      rootDefaultYaml: '',
      rootConfigType: buildCompositeConfigType({
        key: 'root-key',
      }),
      allConfigTypes: [
        buildCompositeConfigType({
          key: 'root-key',
          description: null,
          isSelector: false,
          typeParamKeys: [],
          fields: [
            // No resources field
            buildConfigTypeField({
              name: 'ops',
              description: null,
              isRequired: true,
              configTypeKey: 'ops-key',
              defaultValueAsJson: null,
            }),
          ],
        }),
      ],
    });

    const result = filterDefaultYamlOptionalResources(yamlInput, schema);

    expect(result).toBe(yamlInput);
  });

  it('handles all resources being required', () => {
    const yamlInput = `
resources:
  required_db:
    host: localhost
  required_cache:
    ttl: 300
ops:
  my_op: {}
`;

    const schema = createMockRunConfigSchema([
      {name: 'required_db', isRequired: true},
      {name: 'required_cache', isRequired: true},
    ]);

    const result = filterDefaultYamlOptionalResources(yamlInput, schema);

    expect(result).toContain('required_db');
    expect(result).toContain('required_cache');
    expect(result).toContain('resources');
    expect(result).toContain('ops');
  });
});
