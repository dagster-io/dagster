/* eslint-disable import/no-default-export */

import babel from '@rollup/plugin-babel';
import commonjs from '@rollup/plugin-commonjs';
import image from '@rollup/plugin-image';
import json from '@rollup/plugin-json';
import resolve from '@rollup/plugin-node-resolve';
import url from '@rollup/plugin-url';
import nodeGlobals from 'rollup-plugin-node-globals';
import polyfills from 'rollup-plugin-polyfill-node';
import styles from 'rollup-plugin-styles';

const extensions = ['.js', '.jsx', '.ts', '.tsx', '.css', '.svg'];

export default {
  input: {
    index: './src/index.ts',

    // Our core fonts, usable as global style components, e.g. `<GlobalInconsolata />`.
    GlobalInconsolata: './src/fonts/GlobalInconsolata.tsx',
    GlobalInter: './src/fonts/GlobalInter.tsx',

    // Components are listed here individually so that they may be imported
    // without pulling in the entire library.
    Box: './src/components/Box.tsx',
    Button: './src/components/Button.tsx',
    Colors: './src/components/Colors.tsx',
    Icon: './src/components/Icon.tsx',
  },
  output: {
    dir: 'lib',
    exports: 'named',
    format: 'esm',
    sourcemap: true,
  },
  plugins: [
    styles({
      extract: true,
    }),
    json(),
    url(),
    image(),
    babel({
      babelHelpers: 'bundled',
      exclude: 'node_modules/**',
      extensions: ['.js', '.jsx', '.ts', '.tsx'],
    }),
    commonjs(),
    polyfills(),
    nodeGlobals(),
    resolve({extensions, preferBuiltins: false}),
  ],
  external: [
    '@blueprintjs/core',
    '@blueprintjs/popover2',
    '@blueprintjs/select',
    'react',
    'react-dom',
    'react-is',
    'react-virtualized',
    'styled-components',
  ],
};
