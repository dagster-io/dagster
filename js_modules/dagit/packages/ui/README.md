## Dagster UI Component Library

This project contains the core React UI component library used by Dagster products.

While published as a public package, it is not intended for use outside Dagster code, and is not currently supported for public consumption.

Semver usage is likely to be inconsistent, and new versions may be published with breaking changes without warning.

## Usage

### 1. Install package.

```bash
yarn add @dagster-io/ui
```

Note that the library currently includes a lot of peer dependencies. Be sure to install these.

### 2. Add font styles

If necessary, add font styles to your application root and use them in your global styles.

If you are importing fonts via some other means (e.g. Google Fonts API) you may not need to do this.

```jsx
import {FontFamily, GlobalInter} from '@dagster-io/ui`;
import {createGlobalStyle} from 'styled-components';

const GlobalStyle = createGlobalStyle`
  * {
    font-family: ${FontFamily.default}; /* Default font is Inter */
  }
`;

const MyAppRoot = () => (
  <>
    <GlobalInter />
    <GlobalStyle />
    <div>
      /* Your app */
    </div>
  </>
);
```

### 3. Import components

```jsx
import {Box, Button, Colors, Icon} from '@dagster-io/ui';
```

The rollup build specifies certain common components to be split into their own bundles to allow consumers to minimize their bundle size and avoid importing the entire library, since it currently contains a lot of complex, heavy components that you may not need.

If you find that your import of a specific component has blown up your build size, we can add it to the `input` list in `rollup.config.js` to split it into its own bundle.

### 4. Add Blueprint CSS.

If necessary, add Blueprint CSS. Some components require underlying Blueprint styles. Many do not.

_How do I know if I need Blueprint?_

- Check if the component you are using renders a Blueprint component. If so, include Blueprint CSS.
- If you're not sure, try rendering the component and see if its styles look broken. If so, and the styles involve a `bp3` CSS class, you need Blueprint CSS.

```css
/* blueprint.css */

@import '@blueprintjs/core/lib/css/blueprint.css';
@import '@blueprintjs/icons/lib/css/blueprint-icons.css';
@import '@blueprintjs/select/lib/css/blueprint-select.css';
@import '@blueprintjs/table/lib/css/table.css';
@import '@blueprintjs/popover2/lib/css/blueprint-popover2.css';
```

```jsx
import './blueprint.css';

export const MyAppRoot = () => ...;
```
