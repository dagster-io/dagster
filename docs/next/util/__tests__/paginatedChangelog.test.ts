import {promises as fs} from 'fs';

import {getPaginatedChangeLog} from '../paginatedChangelog';

jest.mock('fs', () => ({
  promises: {
    readFile: jest.fn(),
  },
}));

type TMocked = jest.MockedFn<typeof fs.readFile>;

// Test suite
describe('getPaginatedChangeLog', () => {
  beforeEach(() => {
    (fs.readFile as TMocked).mockClear();
  });

  test('returns paginated changelog and frontMatterData', async () => {
    const content = `# Changelog

# 1.3.0 (core) / 0.19.0 (libraries) "Smooth Operator"

## Header

- Feature A

# 1.2.0

## Another one

- Feature B

# 1.1.0

### Something here

- Feature B
`;

    (fs.readFile as TMocked).mockResolvedValue(content);

    // Each version on its own page
    expect((await getPaginatedChangeLog({versionCountPerPage: 1})).pageContentList)
      .toMatchInlineSnapshot(`
      [
        "# Changelog

      # 1.3.0 (core) / 0.19.0 (libraries) "Smooth Operator"

      ## Header

      - Feature A
      ",
        "# Changelog

      # 1.2.0

      ## Another one

      - Feature B
      ",
        "# Changelog

      # 1.1.0

      ### Something here

      - Feature B
      ",
      ]
    `);

    // Two pages in total, where the second page is shorter
    expect((await getPaginatedChangeLog({versionCountPerPage: 2})).pageContentList)
      .toMatchInlineSnapshot(`
      [
        "# Changelog

      # 1.3.0 (core) / 0.19.0 (libraries) "Smooth Operator"

      ## Header

      - Feature A

      # 1.2.0

      ## Another one

      - Feature B
      ",
        "# Changelog

      # 1.1.0

      ### Something here

      - Feature B
      ",
      ]
    `);

    // Only one page
    const singlePageResult = await getPaginatedChangeLog({versionCountPerPage: 20});
    expect(singlePageResult.pageContentList).toHaveLength(1);
    expect(singlePageResult.pageContentList[0]).toEqual(content);
  });
});
