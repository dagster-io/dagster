/// <reference types="next" />
/// <reference types="next/types/global" />

declare module '@mdx-js/mdx' {
  function createCompiler(): {
    // NOTE: this can be typed better...
    parse: (input: string) => any;
  };
}
