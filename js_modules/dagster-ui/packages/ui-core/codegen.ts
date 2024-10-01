import {CodegenConfig} from '@graphql-codegen/cli';

const config: CodegenConfig = {
  schema: './src/graphql/schema.graphql',
  documents: ['src/**/*.tsx'],
  ignoreNoDocuments: true, // for better experience with the watcher
  hooks: {
    afterAllFileWrite: ['prettier --write'],
  },
  generates: {
    './src/graphql/types.ts': {
      config: {
        nonOptionalTypename: true,
        avoidOptionals: {
          field: true,
        },
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
        {
          'typescript-mock-data': {
            addTypename: true,
            prefix: 'build',
            listElementCount: 0,
            typeNames: 'keep',
            enumValues: 'keep',
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
