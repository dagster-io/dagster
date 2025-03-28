import {describe, it, expect} from 'vitest';
import {dedentLines, filterComments, trimMainBlock} from './codeExampleUtils';

describe('filterComments', () => {
  it('should remove noqa comments from lines', () => {
    const input = [
      'def example_function():  # noqa',
      '    x = 5  # some comment with noqa: F401 in it',
      '    y = 10  # regular comment',
      '    print(x + y)  # noqa: F401, E501',
      '    # noqa: this is all comment',
    ];

    const expected = ['def example_function():', '    x = 5', '    y = 10  # regular comment', '    print(x + y)', ''];

    expect(filterComments(input)).toEqual(expected);
  });

  it('should remove type: ignore comments from lines', () => {
    const input = [
      'from typing import Dict, Any  # type: ignore',
      'x: Dict[str, Any] = {}  # type: ignore[valid-type]',
      'y = 10  # regular comment',
      'z = "test"  # type: ignore # and more comments',
    ];

    const expected = [
      'from typing import Dict, Any',
      'x: Dict[str, Any] = {}',
      'y = 10  # regular comment',
      'z = "test"',
    ];

    expect(filterComments(input)).toEqual(expected);
  });

  it('should remove isort: skip_file comments from lines', () => {
    const input = [
      '# isort: skip_file',
      'from typing import Dict, Any  # isort: skip',
      'from typing import Dict, Any  # isort:skip',
    ];

    const expected = ['', 'from typing import Dict, Any', 'from typing import Dict, Any'];

    expect(filterComments(input)).toEqual(expected);
  });

  it('should handle empty input array', () => {
    expect(filterComments([])).toEqual([]);
  });

  it('should handle lines without ignored comments', () => {
    const input = ['def example_function():', '    x = 5  # some comment', '    y = 10', '    print(x + y)'];

    expect(filterComments(input)).toEqual(input);
  });
});

describe('trimMainBlock', () => {
  it('should remove content below if __name__ block', () => {
    const input = [
      'import os',
      'import sys',
      '',
      'def main():',
      '    print("Hello, world!")',
      '',
      'if __name__ == "__main__":',
      '    main()',
      '    print("This should be removed")',
    ];

    const expected = ['import os', 'import sys', '', 'def main():', '    print("Hello, world!")', ''];

    expect(trimMainBlock(input)).toEqual(expected);
  });

  it('should handle input without if __name__ block', () => {
    const input = ['import os', 'import sys', '', 'def main():', '    print("Hello, world!")', '', 'main()'];

    expect(trimMainBlock(input)).toEqual(input);
  });

  it('should handle empty input array', () => {
    expect(trimMainBlock([])).toEqual([]);
  });

  it('should handle if __name__ with different spacing', () => {
    const input = ['import os', '', 'def main():', '    pass', 'if    __name__    ==    "__main__":', '    main()'];

    const expected = ['import os', '', 'def main():', '    pass'];

    expect(trimMainBlock(input)).toEqual(expected);
  });
});

describe('dedent', () => {
  it('should remove leading spaces based on dedentAmount', () => {
    const input = ['    line one', '    line two', '      line three'];
    const dedentAmount = 4;
    const expected = ['line one', 'line two', '  line three'];
    expect(dedentLines(input, dedentAmount)).toEqual(expected);
  });

  it('should return the same lines if no indentation matches', () => {
    const input = ['line one', 'line two', 'line three'];
    const dedentAmount = 4;
    const expected = input;
    expect(dedentLines(input, dedentAmount)).toEqual(expected);
  });

  it('should handle empty lines', () => {
    const input = ['    line one', '', '    line two'];
    const dedentAmount = 4;
    const expected = ['line one', '', 'line two'];
    expect(dedentLines(input, dedentAmount)).toEqual(expected);
  });

  it('should handle no lines', () => {
    const input: string[] = [];
    const dedentAmount = 4;
    const expected: string[] = [];
    expect(dedentLines(input, dedentAmount)).toEqual(expected);
  });
});
