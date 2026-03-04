import {CodegenConfig} from '@graphql-codegen/cli';

const config: CodegenConfig = {
  schema: './src/graphql/schema.graphql',
  documents: ['src/**/*.tsx'],
  ignoreNoDocuments: true, // for better experience with the watcher
  hooks: {
    afterAllFileWrite: ['prettier --write'],
  },
  generates: {
    // To be deleted once existing imports are updated to use fragments.
    './src/graphql/types-do-not-use.ts': {
      config: {
        nonOptionalTypename: true,
        avoidOptionals: {
          field: true,
        },
        enumValues: './types',
        dedupeFragments: true,
        namingConvention: {
          enumValues: 'keep',
        },
        useImplementingTypes: true,
      },
      plugins: [
        'typescript',
        {
          add: {
            content: `// Generated GraphQL types, do not edit manually.\n`,
          },
        },
      ],
    },
    './src/graphql/types.ts': {
      config: {
        onlyOperationTypes: true,
        namingConvention: {
          enumValues: 'keep',
        },
      },
      plugins: [
        'typescript',
        {
          add: {
            content: `// Generated GraphQL enums, do not edit manually.\n`,
          },
        },
      ],
    },
    './src/graphql/builders.ts': {
      config: {
        nonOptionalTypename: true,
        avoidOptionals: {
          field: true,
        },
        enumValues: './types',
        dedupeFragments: true,
        namingConvention: {
          enumValues: 'keep',
        },
        useImplementingTypes: true,
        noExport: true,
      },
      plugins: [
        'typescript',
        {
          add: {
            content: `// Generated GraphQL builders, do not edit manually.\n`,
          },
        },
        {
          'typescript-mock-data': {
            addTypename: true,
            prefix: 'build',
            enumValues: 'keep',
            listElementCount: 0,
            terminateCircularRelationships: true,
            useImplementingTypes: true,
          },
        },
      ],
    },
    './src/': {
      preset: 'near-operation-file',
      presetConfig: {
        extension: '.types.ts',
        folder: 'types',
        baseTypesPath: './graphql/types.ts',
      },
      config: {
        dedupeOperationSuffix: true,
        nonOptionalTypename: true,
        avoidOptionals: {
          field: true,
        },
      },
      plugins: [
        'typescript-operations',
        {
          add: {
            content: `// Generated GraphQL types, do not edit manually.\n`,
          },
        },
      ],
    },
    './client.json': {
      plugins: [
        {
          'persisted-query-ids': {
            algorithm: 'sha256',
            output: 'client',
          },
        },
      ],
    },
  },
};

// eslint-disable-next-line import/no-default-export
export default config;
