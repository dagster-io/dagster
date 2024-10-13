# VS Code editor settings

If you use VS Code, we recommend the following configuration:

## Step 1: Install the recommended extensions

The [recommended extensions](.vscode/extensions.json) will automatically show up when browsing
extensions for your editor. Install them.

See [VS Code's documentation on recommended extensions](https://code.visualstudio.com/docs/editor/extension-marketplace#_workspace-recommended-extensions)
to add new extensions to the recommended list.

## Step 2: Enable the default editor settings

The recommended editor settings, [`settings.json.default`](.vscode/settings.json.default), are not enabled by default. To
enable the default settings, copy the file to `.vscode/settings.json` to enable them for this
repository. These settings will override any existing user or workspace settings you have already
configured.

If you already have existing settings, you can instead copy specific configuration from the
recommended editor settings to your user or workspace settings.

See the [settings precedence](https://code.visualstudio.com/docs/getstarted/settings#_settings-precedence) for more details.

Likewise, the recommended debugger entrypoints, [`launch.json.default`](.vscode/launch.json.default)
and [`tasks.json.default`](.vscode/tasks.json.default), are not enabled by default. To enable the
default, copy these files to `.vscode/launch.json` and `.vscode/tasks.json`.
