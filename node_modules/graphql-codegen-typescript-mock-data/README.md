# graphql-codegen-typescript-mock-data

## Description

[GraphQL Codegen Plugin](https://github.com/dotansimha/graphql-code-generator) for building mock data based on the schema.

## Installation

`yarn add -D graphql-codegen-typescript-mock-data`

## Configuration

### typesFile (`string`, defaultValue: `null`)

Defines the file path containing all GraphQL types. This file can also be generated through graphql-codgen

### addTypename (`boolean`, defaultValue: `false`)

Adds `__typename` property to mock data

### enumsAsTypes (`boolean`, defaultValue: `false`)

Changes enums to TypeScript string union types

### terminateCircularRelationships (`boolean`, defaultValue: `false`)

When enabled, prevents circular relationships from triggering infinite recursion. After the first resolution of a
specific type in a particular call stack, subsequent resolutions will return an empty object cast to the correct type.

### prefix (`string`, defaultValue: `a` for constants & `an` for vowels)

The prefix to add to the mock function name. Cannot be empty since it will clash with the associated
typescript definition from `@graphql-codegen/typescript`

### listElementCount (`number`, defaultValue: `1`)

How many elements should be generated for lists. For example, with `listElementCount: 3` a schema field `names: [String!]!` would generate `3` names in each mock.

### enumValues (`string`, defaultValue: `change-case-all#pascalCase`)

Changes the case of the enums. The format of the converter must be a valid `module#method`. You can also use `keep` to
keep all GraphQL names as-is. Available case functions in `change-case-all` are `camelCase`, `capitalCase`, `constantCase`,
`dotCase`, `headerCase`, `noCase`, `paramCase`, `pascalCase`, `pathCase`, `sentenceCase`, `snakeCase`, `lowerCase`,
`localeLowerCase`, `lowerCaseFirst`, `spongeCase`, `titleCase`, `upperCase`, `localeUpperCase` and `upperCaseFirst`
[See more](https://github.com/btxtiger/change-case-all)

### typeNames (`string`, defaultValue: `change-case-all#pascalCase`)

Changes the case of types. The format of the converter must be a valid `module#method`. You can also use `keep` to
keep all GraphQL names as-is. Available case functions in `change-case-all` are `camelCase`, `capitalCase`, `constantCase`,
`dotCase`, `headerCase`, `noCase`, `paramCase`, `pascalCase`, `pathCase`, `sentenceCase`, `snakeCase`, `lowerCase`,
`localeLowerCase`, `lowerCaseFirst`, `spongeCase`, `titleCase`, `upperCase`, `localeUpperCase` and `upperCaseFirst`
[See more](https://github.com/btxtiger/change-case-all)

### scalars (`{ [Scalar: string]: GeneratorOptions }`, defaultValue: `undefined`)

Allows you to define mappings for your custom scalars. Allows you to map any GraphQL Scalar to a
[casual](https://github.com/boo1ean/casual#embedded-generators) embedded generator (string or
function key) with optional arguments, or a or [faker](https://fakerjs.dev/api/) generator with optional arguments

For detailed configuration options, see [GeneratorOptions](#generatoroptions-type) documentation.

Examples using **casual**

```yaml
plugins:
  - typescript-mock-data:
      scalars:
        Date: date # gets translated to casual.date()
```

**With arguments**

```yaml
plugins:
  - typescript-mock-data:
      scalars:
        Date: # gets translated to casual.date('YYYY-MM-DD')
          generator: date
          arguments: 'YYYY-MM-DD'
```

Examples using **faker**

```yaml
plugins:
  - typescript-mock-data:
      scalars:
        Date: date.past # gets translated to faker.date.past()
```

**With arguments**

```yaml
plugins:
  - typescript-mock-data:
      scalars:
        Date: # gets translated to faker.date.past(10)
          generator: date.past
          arguments: 10
```

**Custom value generator**

```yaml
plugins:
  - add: "import { arrayBufferGenerator } from '../generators';"
  - typescript-mock-data:
      scalars:
        ArrayBuffer: arrayBufferGenerator()
```

### typesPrefix (`string`, defaultValue: '')

Useful if you have globally exported types under a certain namespace.
e.g If the types file is something like this

```
declare namespace Api {
 type User {
  ...
 }
}
```

Setting the `typesPrefix` to `Api.` will create the following mock data

```
export const aUser = (overrides?: Partial<Api.User>): Api.User => {
```

### enumsPrefix (`string`, defaultValue: '')

Similar to `typesPrefix`, but for enum types

```
declare namespace Api {
 enum Status {
  ...
 }
}
```

Setting the `enumsPrefix` to `Api.` will create the following mock data

```
export const aUser = (overrides?: Partial<User>): User => {
   status: overrides && overrides.hasOwnProperty('status') ? overrides.status! : Api.Status.Online,
}
```

### transformUnderscore (`boolean`, defaultValue: `true`)

When disabled, underscores will be retained for type names when the case is changed. It has no effect if `typeNames` is set to `keep`.

### dynamicValues (`boolean`, defaultValue: `false`)

When enabled, values will be generated dynamically when the mock function is called rather than statically when the mock function is generated. The values are generated consistently from a [casual seed](https://github.com/boo1ean/casual#seeding) that can be manually configured using the generated `seedMocks(seed: number)` function, as shown in [this test](https://github.com/JimmyPaolini/graphql-codegen-typescript-mock-data/blob/dynamic-mode/tests/dynamicValues/spec.ts#L13).

### fieldGeneration (`{ [typeName: string]: { [fieldName: string]: GeneratorOptions } }`, defaultValue: `undefined`)

This setting allows you to add specific generation to a field for a given type. For example if you have a type called `User` and a field called `birthDate` you can override any generated value there as follows:

```yaml
plugins:
  - typescript-mock-data:
      scalars:
        Date: date.future
      fieldGeneration:
        User:
          birthDate: date.past
```

Note that even if `birthDate` is a scalar of `Date` type, its value will still be overridden.

If you want to use a specific generator for **all** fields of a given name, you can declare it under a property called `_all`:

```yaml
plugins:
  - typescript-mock-data:
      scalars:
        Date: date.future
      fieldGeneration:
        _all:
          email: internet.email
        AdminUser:
          email: 'admin@email.com'
```

In the above example all resolvers with the name `email` will use the `internet.email` generator. However since we specified a specific email for `AdminUser` that will take precedence over the `_all` generated value.

For detailed configuration options, see [GeneratorOptions](#generatoroptions-type) documentation.

### generateLibrary (`'casual' | 'faker'`, defaultValue: `'casual'`)

Select a library to generate mock values. The default is [casual](https://github.com/boo1ean/casual), Other options include [faker](https://github.com/faker-js/faker).
casual dependents on Node API and cannot be executed in a browser. faker is useful when you want to use a mock function with the dynamicValues option enabled in the browser.

### `GeneratorOptions` type

This type is used in `scalars` and `fieldGeneration` options.

Examples using **casual**

**Shorthand if you don't have arguments**

```yaml
fieldName: date # gets translated to casual.date()
```

**With arguments**

```yaml
fieldName: # gets translated to casual.date('YYYY-MM-DD')
  generator: date
  arguments: 'YYYY-MM-DD'
```

**With multiple arguments**

```yaml
fieldName: # gets translated to casual.integer(-100, 100)
  generator: integer
  arguments:
    - -100
    - 100
```

**With extra function call**

```yaml
fieldName: # gets translated to casual.integer.toFixed()
  generator: integer
  extra:
    function: toFixed
```

**With extra function call arguments**

```yaml
fieldName: # gets translated to casual.integer.toFixed(3)
  generator: integer
  extra:
    function: toFixed
    arguments: 3
```

Examples using **faker**

**With arguments**

```yaml
plugins:
  - typescript-mock-data:
      scalars:
        Date: # gets translated to faker.date.past(10)
          generator: date.past
          arguments: 10
```

**With multiple arguments**

```yaml
plugins:
  - typescript-mock-data:
      scalars:
        Description: # gets translated to faker.lorem.paragraphs(3, '\n')
          generator: lorem.paragraphs
          arguments:
            - 3
            - '\n'
```

**Shorthand if you don't have arguments**

```yaml
plugins:
  - typescript-mock-data:
      scalars:
        Date: date.past # gets translated to faker.date.past()
```

**With extra function call**

```yaml
fieldName: # gets translated to casual.date().toLocaleDateString()
  generator: date
  extra:
    function: toLocaleDateString
```

**With extra function call arguments**

```yaml
fieldName: # gets translated to casual.date().toLocaleDateString('en_GB)
  generator: date
  extra:
    function: toLocaleDateString
    arguments: 'en_GB'
```

**Custom value generator**

```yaml
# gets translated as is
fieldName: arrayBufferGenerator()
```

## Examples of usage

**codegen.yml**

```yaml
overwrite: true
schema: schema.graphql
generates:
  src/generated-types.ts:
    plugins:
      - 'typescript'
  src/mocks/generated-mocks.ts:
    plugins:
      - typescript-mock-data:
          typesFile: '../generated-types.ts'
          enumValues: upper-case#upperCase
          typeNames: keep
          scalars:
            AWSTimestamp: unix_time # gets translated to casual.unix_time
```

### With `eslint-disable` rule

**codegen.yml**

```yaml
overwrite: true
schema: schema.graphql
generates:
  src/generated-types.ts:
    plugins:
      - 'typescript'
  src/mocks/generated-mocks.ts:
    plugins:
      - add:
          content: '/* eslint-disable @typescript-eslint/no-use-before-define,@typescript-eslint/no-unused-vars,no-prototype-builtins */'
      - typescript-mock-data:
          typesFile: '../generated-types.ts'
          enumValues: upper-case#upperCase
          typeNames: keep
          scalars:
            AWSTimestamp: unix_time # gets translated to casual.unix_time
```

## Example of generated code

Given the following schema:

```graphql
scalar AWSTimestamp

type Avatar {
  id: ID!
  url: String!
}

type User {
  id: ID!
  login: String!
  avatar: Avatar
  status: Status!
  updatedAt: AWSTimestamp
}

type Query {
  user: User!
}

input UpdateUserInput {
  id: ID!
  login: String
  avatar: Avatar
}

enum Status {
  ONLINE
  OFFLINE
}

type Mutation {
  updateUser(user: UpdateUserInput): User
}
```

The code generated will look like:

```typescript
export const anAvatar = (overrides?: Partial<Avatar>): Avatar => {
  return {
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : '0550ff93-dd31-49b4-8c38-ff1cb68bdc38',
    url: overrides && overrides.hasOwnProperty('url') ? overrides.url! : 'aliquid',
  };
};

export const anUpdateUserInput = (overrides?: Partial<UpdateUserInput>): UpdateUserInput => {
  return {
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : '1d6a9360-c92b-4660-8e5f-04155047bddc',
    login: overrides && overrides.hasOwnProperty('login') ? overrides.login! : 'qui',
    avatar: overrides && overrides.hasOwnProperty('avatar') ? overrides.avatar! : anAvatar(),
  };
};

export const aUser = (overrides?: Partial<User>): User => {
  return {
    id: overrides && overrides.hasOwnProperty('id') ? overrides.id! : 'a5756f00-41a6-422a-8a7d-d13ee6a63750',
    login: overrides && overrides.hasOwnProperty('login') ? overrides.login! : 'libero',
    avatar: overrides && overrides.hasOwnProperty('avatar') ? overrides.avatar! : anAvatar(),
    status: overrides && overrides.hasOwnProperty('status') ? overrides.status! : Status.Online,
    updatedAt: overrides && overrides.hasOwnProperty('updatedAt') ? overrides.updatedAt! : 1458071232,
  };
};
```

### Usage in tests

Those helper functions can be used in our unit tests:

```typescript
const user = aUser({ login: 'johndoe' });

// will create a user object with `login` property overridden to `johndoe`
```

### Dealing with Timezone

If some properties use generated dates, the result could different depending on the timezone of your machine.

To force a timezone, you can set environment variable `TZ`:

```bash
TZ=UTC graphql-codegen
```

This will force the timezone to `UTC`, whatever the timezone of your machine or CI

### Contributing

Feel free to open issues and pull requests. We always welcome support from the community.

To run this project locally:

- Use Node >= 10
- Make sure that you have the latest Yarn version (https://yarnpkg.com/lang/en/docs/install/)
- Clone this repo using `git clone`
- Run `yarn`
- Run `yarn build` to build the package
- Run `yarn test` to make sure everything works

### License

[![GitHub license](https://img.shields.io/badge/license-MIT-lightgrey.svg?maxAge=2592000)](https://raw.githubusercontent.com/ardeois/graphql-codegen-typescript-mock-data/master/LICENSE)

MIT
