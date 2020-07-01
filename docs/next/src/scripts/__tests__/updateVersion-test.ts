import { updateVersionsJson, generateVersionsMDX } from '../updateVersion';

const MOCK_JSON_CONTENT = {
  currentVersion: {
    version: '0.7.13',
    documentation: '/docs/install',
    releaseNotes: 'https://github.com/dagster-io/dagster/releases/tag/0.7.13',
  },
  allVersions: [
    {
      version: '0.7.13',
      documentation: '/0.7.13/docs/install',
      releaseNotes: 'https://github.com/dagster-io/dagster/releases/tag/0.7.13',
    },
    {
      version: '0.7.12',
      documentation: '/0.7.12/docs/install',
      releaseNotes: 'https://github.com/dagster-io/dagster/releases/tag/0.7.12',
    },
    {
      version: '0.7.11',
      documentation: '/0.7.11/docs/install',
      releaseNotes: 'https://github.com/dagster-io/dagster/releases/tag/0.7.11',
    },
    {
      version: '0.7.10',
      documentation: '/0.7.10/docs/install',
      releaseNotes: 'https://github.com/dagster-io/dagster/releases/tag/0.7.10',
    },
    {
      version: '0.7.9',
      documentation: '/0.7.9/docs/install',
      releaseNotes: 'https://github.com/dagster-io/dagster/releases/tag/0.7.9',
    },
    {
      version: '0.7.8',
      documentation: 'https://dagster.readthedocs.io/en/0.7.8/',
      releaseNotes: 'https://github.com/dagster-io/dagster/releases/tag/0.7.8',
      note: 'Documentation is on external site',
    },
  ],
};

test('updateVersionsJson works', () => {
  // TODO: Fix update versions
  return;

  const { oldVersion, newJsonContent } = updateVersionsJson(
    JSON.stringify(MOCK_JSON_CONTENT),
    '0.7.100',
  );
  expect(oldVersion).toEqual('0.7.13');
  expect(newJsonContent).toMatchInlineSnapshot(`
    "{
        \\"currentVersion\\": {
            \\"version\\": \\"0.7.100\\",
            \\"documentation\\": \\"/docs/install\\",
            \\"releaseNotes\\": \\"https://github.com/dagster-io/dagster/releases/tag/0.7.100\\"
        },
        \\"allVersions\\": [
            {
                \\"version\\": \\"0.7.100\\",
                \\"documentation\\": \\"/0.7.100/docs/install\\",
                \\"releaseNotes\\": \\"https://github.com/dagster-io/dagster/releases/tag/0.7.100\\"
            },
            {
                \\"version\\": \\"0.7.13\\",
                \\"documentation\\": \\"/0.7.13/docs/install\\",
                \\"releaseNotes\\": \\"https://github.com/dagster-io/dagster/releases/tag/0.7.13\\"
            },
            {
                \\"version\\": \\"0.7.12\\",
                \\"documentation\\": \\"/0.7.12/docs/install\\",
                \\"releaseNotes\\": \\"https://github.com/dagster-io/dagster/releases/tag/0.7.12\\"
            },
            {
                \\"version\\": \\"0.7.11\\",
                \\"documentation\\": \\"/0.7.11/docs/install\\",
                \\"releaseNotes\\": \\"https://github.com/dagster-io/dagster/releases/tag/0.7.11\\"
            },
            {
                \\"version\\": \\"0.7.10\\",
                \\"documentation\\": \\"/0.7.10/docs/install\\",
                \\"releaseNotes\\": \\"https://github.com/dagster-io/dagster/releases/tag/0.7.10\\"
            },
            {
                \\"version\\": \\"0.7.9\\",
                \\"documentation\\": \\"/0.7.9/docs/install\\",
                \\"releaseNotes\\": \\"https://github.com/dagster-io/dagster/releases/tag/0.7.9\\"
            },
            {
                \\"version\\": \\"0.7.8\\",
                \\"documentation\\": \\"https://dagster.readthedocs.io/en/0.7.8/\\",
                \\"releaseNotes\\": \\"https://github.com/dagster-io/dagster/releases/tag/0.7.8\\",
                \\"note\\": \\"Documentation is on external site\\"
            }
        ]
    }"
  `);
});

test('updateMDX works', () => {
  // TODO: Fix update versions
  return;

  expect(generateVersionsMDX(JSON.stringify(MOCK_JSON_CONTENT)).mdxContent)
    .toMatchInlineSnapshot(`
    "# Dagster Versions

    ## Current version (Stable)

    | **0.7.13** | [Documentation](/docs/install) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.13) |
    | ---- | ---- | ---- |


    ## All Versions

    | **0.7.13** | [Documentation](/0.7.13/docs/install) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.13) |   |
    | ---- | ---- | ---- | ---- |
    | **0.7.12** | [Documentation](/0.7.12/docs/install) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.12) |   |
    | **0.7.11** | [Documentation](/0.7.11/docs/install) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.11) |   |
    | **0.7.10** | [Documentation](/0.7.10/docs/install) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.10) |   |
    | **0.7.9** | [Documentation](/0.7.9/docs/install) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.9) |   |
    | **0.7.8** | [Documentation](https://dagster.readthedocs.io/en/0.7.8/) | [Release Notes](https://github.com/dagster-io/dagster/releases/tag/0.7.8) | Documentation is on external site |"
  `);
});
