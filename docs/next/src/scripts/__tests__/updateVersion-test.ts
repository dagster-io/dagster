import { updateVersion } from '../updateVersion';

const MOCK_CONTENT = `# Dagster Versions

## Current version (Stable)

| **0.7.12** | [Documentation](/docs/install) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.12) |
| ---------- | ------------------------------ | -------------------------------------------------------------------------- |


## All Versions

| **0.7.12** | [Documentation](/0.7.12/docs/install)                     | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.12) |                                         |
| ---------- | --------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------- |
| **0.7.11** | [Documentation](/0.7.11/docs/install)                     | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.11) |                                         |
| **0.7.10** | [Documentation](/0.7.10/docs/install)                     | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.10) |                                         |
| **0.7.9**  | [Documentation](/0.7.9/docs/install)                      | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.9)  |                                         |
| **0.7.8**  | [Documentation](https://dagster.readthedocs.io/en/0.7.8/) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.8)  | Note: Documentation is on external site |
| **0.7.7**  | [Documentation](https://dagster.readthedocs.io/en/0.7.7/) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.7)  | Note: Documentation is on external site |
`;

const MOCK_NEW_CONTENT = `# Dagster Versions

## Current version (Stable)

| **0.7.100** | [Documentation](/docs/install) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.100) |
| ---------- | ------------------------------ | -------------------------------------------------------------------------- |


## All Versions

| **0.7.100** | [Documentation](/0.7.100/docs/install)                     | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.100) |                                         |
| ---------- | --------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------- |
| **0.7.12** | [Documentation](/0.7.12/docs/install)                     | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.12) |                                         |
| **0.7.11** | [Documentation](/0.7.11/docs/install)                     | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.11) |                                         |
| **0.7.10** | [Documentation](/0.7.10/docs/install)                     | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.10) |                                         |
| **0.7.9**  | [Documentation](/0.7.9/docs/install)                      | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.9)  |                                         |
| **0.7.8**  | [Documentation](https://dagster.readthedocs.io/en/0.7.8/) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.8)  | Note: Documentation is on external site |
| **0.7.7**  | [Documentation](https://dagster.readthedocs.io/en/0.7.7/) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.7)  | Note: Documentation is on external site |
`;

test('it works', () => {
  expect(updateVersion(MOCK_CONTENT, '0.7.100')).toEqual({
    oldVersion: '0.7.12',
    newContent: MOCK_NEW_CONTENT,
  });
});
