import {describe, it, expect} from 'vitest';
import {filterNoqaComments, trimMainBlock} from './codeExampleUtils';

describe('filterNoqaComments', () => {
  it('should remove noqa comments from lines', () => {
    const input = [
      'def example_function():  # noqa',
      '    x = 5  # some comment with noqa: F401 in it',
      '    y = 10  # regular comment',
      '    print(x + y)  # noqa: F401, E501',
      '    # noqa: this is all comment',
    ];

    const expected = [
      'def example_function():',
      '    x = 5',
      '    y = 10  # regular comment',
      '    print(x + y)',
      '',
    ];

    expect(filterNoqaComments(input)).toEqual(expected);
  });

  it('should handle empty input array', () => {
    expect(filterNoqaComments([])).toEqual([]);
  });

  it('should handle lines without noqa comments', () => {
    const input = [
      'def example_function():',
      '    x = 5  # some comment',
      '    y = 10',
      '    print(x + y)',
    ];

    expect(filterNoqaComments(input)).toEqual(input);
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

    const expected = [
      'import os',
      'import sys',
      '',
      'def main():',
      '    print("Hello, world!")',
      '',
    ];

    expect(trimMainBlock(input)).toEqual(expected);
  });

  it('should handle input without if __name__ block', () => {
    const input = [
      'import os',
      'import sys',
      '',
      'def main():',
      '    print("Hello, world!")',
      '',
      'main()',
    ];

    expect(trimMainBlock(input)).toEqual(input);
  });

  it('should handle empty input array', () => {
    expect(trimMainBlock([])).toEqual([]);
  });

  it('should handle if __name__ with different spacing', () => {
    const input = [
      'import os',
      '',
      'def main():',
      '    pass',
      'if    __name__    ==    "__main__":',
      '    main()',
    ];

    const expected = [
      'import os',
      '',
      'def main():',
      '    pass',
    ];

    expect(trimMainBlock(input)).toEqual(expected);
  });
});
