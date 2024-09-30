# 1.1.3 (September 25, 2024)

- Revert Rollup upgrade

# 1.1.2 (September 25, 2024)

- Upgrade to Rollup 4
- Expose all icons from icon-svgs directory

## 1.1.1 (September 24, 2024)

- Add `DateRangePickerWrapper` export

## 1.1.0 (September 10, 2024)

- Add `VirtualizedTable` export
- A whole lot of stuff, including switching from Inter/Inconsolata to Geist fonts.

## 1.0.9 (June 12, 2023)

- Upgrade to Storybook 7
- Move stories and tests into folders
- Support React 18
  - Update props interfaces to explicitly include `children`
  - Make `Toaster` creation async
- Upgrade to React 18
- Upgrade to Blueprint 4
- New components
  - `ErrorBoundary` wrapper component
  - `RadioContainer`
  - `SubwayDot`
  - `TagSelector`
  - `VirtualizedTable` cell and row components
- Add `useViewport` hook
- Remove `Markdown` component to eliminate dependency
- Add a bunch of new icons
- Add icon-less state to `NonIdealState`
- Fix a few bugs with `MiddleTruncate`
- Fix `Countdown` to show minutes/hours, not just total seconds
- Change default `Table` font to no longer be monospace

## 1.0.8 (January 9, 2023)

- Added ProductTour component
- Build CJS output instead of ESM, with individual built components in subdirectories
- Bump dependencies
- Repair `MiddleTruncate` for Firefox

## 1.0.7 (October 31, 2022)

- Added partition icon
- ConfigEditorHelp now highlights types and their descriptions as you hover over them. This makes it easier to discern which comment description belongs to which type.

## 1.0.6 (October 25, 2022)

- Allow overriding colored SVGs with a custom color
- Add right padding to clearable text input to avoid text overlapping button
- Support `12` as an `Icon` size
- Repair CodeMirror hints when rendered within a `Dialog`
- Add `MiddleTruncate`
- Allow `Table` not to use monospace font
- New icons: `asset_plot`, `noteable_logo`, `add`, `subtract`, `forum`, `concept-book`, `youtube`, `chat-support`, `github`, `github_pr_closed`, `github_pr_merged`, `github_pr_open`
- Make pretty-printing JSON a bit more defensive against invalid JSON
- Add a prop to `Tooltip` to fix disabled button issues
- Support dark background on `MetadataTable`, e.g. for tooltip contents
- Swap `CursorControls` buttons for "Older"/"Newer"
- Support `Spinner` as a `Tag` "icon"
- Use dark gray background for `Toast` by default, and dark blue for "success" intent
- Use `JoinedButton` "segmented" control style for `ButtonGroup`
- Fix disabled `Button`, which should not have a visible "active" state
- Repair nullable config types in `ConfigEditor` yaml typeahead
- Add ability to supply `TokenizingField` with raw tokens
- Add `canShow` prop to `Tooltip`, simplifying situations where a tooltip may or may not be rendered on a component
- In CodeMirror yaml mode, send editor to `checkConfig` as-is, without parsing to JSON
- Ensure that `JoinedButtons` can support buttons within `Popover` or other wrapper components

## 1.0.5 (June 16, 2022)

- Add `ConfigEditor`, `StyledCodeMirror`, and associated components
- Add `JoinedButtons`
- Allow `ButtonGroup` to accept number IDs
- Repair `TextInput` font size in Safari
- Add `TextArea`
- Expose `StyledTagInput`
- Fix blocked scroll behavior on `BaseTag`
- Add new icons for assets, graphs
- Make disabled and checked states more obvious for `Switch`
- Fix header alignment on `Dialog`
- Allow `TextInput` to have type `"number"`
- Update tsconfig to `es2022`
- Add a default title to `Spinner`

## 1.0.4 (April 28, 2022)

- Create a build-specific `tsconfig` that excludes `stories` and `test` files
- Clean up `lodash` imports
- Update `workspaces` icon
- Fix rendering of `Suggest` component lists
- Add `topBorder` prop to `DialogFooter`
- Remove `HighlightedCodeBlock`
- Allow `:` character in tag values for `TokenizingField`
- Add Slack icon
- Use `@dagster-io/eslint-config`

## 1.0.3 (April 6, 2022)

- Remove work-in-progress suffixes on components
- Remove react-router-dependent components
- Clean up dependencies

## 1.0.2 (April 4, 2022)

- Publish a JS build with Rollup
- Generate TypeScript type definitions
- Add more details to README

## 1.0.1

- Create README
- Update package metadata

## 1.0.0

Initial package creation.
