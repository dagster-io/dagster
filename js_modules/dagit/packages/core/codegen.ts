import {CodegenConfig} from '@graphql-codegen/cli';

const config: CodegenConfig = {
  schema: './src/graphql/schema.graphql',
  documents: ['src/**/*.tsx'],
  ignoreNoDocuments: true, // for better experience with the watcher
  generates: {
    './src/graphql/': {
      preset: 'client',
      config: {
        avoidOptionals: {
          field: true,
        },
        dedupeFragments: true,
        nonOptionalTypename: true,
        namingConvention: {
          enumValues: 'keep',
        },
      },
      presetConfig: {
        fragmentMasking: false,
      },
      plugins: [],
    },
  },
};

// eslint-disable-next-line import/no-default-export
export default config;
