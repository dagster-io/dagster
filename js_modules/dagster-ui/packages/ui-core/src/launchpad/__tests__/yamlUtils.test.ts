import {mergeYaml} from '../yamlUtils';

describe('yamlUtils.mergeYaml', () => {
  it('should not duplicate array contents', () => {
    const a = `hello:
  - 1
  - a: "object"
  - 3`;

    const b = `hello:
  - 1
  - a: "object"
  - 4`;

    const c = `hello:
  - 1
  - a: 'object'
  - 3
  - 4
`;
    expect(mergeYaml(a, b)).toEqual(c);
  });

  it('should quote strings that may be mis-interpreted', () => {
    const a = `hello: "5:30"`;
    const b = `world: 4`;
    const c = `hello: '5:30'\nworld: 4\n`;
    expect(mergeYaml(a, b)).toEqual(c);
  });
});
