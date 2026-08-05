# How to set up ANTLR

## Install Java

Using M1 MacBook and Homebrew.

Install java:

```bash
$ brew install openjdk
```

Verify it's installed:

```bash
$ $(brew --prefix openjdk)/bin/java --version
```

Verify it's for the arm64 hardware:

```bash
$ file $(brew --prefix openjdk)/bin/java
```

Create symlink:

```bash
$ sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk
$ java -version
```

## Install ANTLR

https://github.com/antlr/antlr4/blob/master/doc/getting-started.md

1. Download:

```bash
$ cd /usr/local/lib
$ curl -O https://www.antlr.org/download/antlr-4.13.2-complete.jar
```

2. Add antlr-4.13.2-complete.jar to your `CLASSPATH`:

```bash
$ export CLASSPATH=".:/usr/local/lib/antlr-4.13.2-complete.jar:$CLASSPATH"
```

Also add to `.bash_profile` or whatever your startup script is.

3. Create alias for ANTLR:

```bash
$ alias antlr4='java -Xmx500M -cp "/usr/local/lib/antlr-4.13.2-complete.jar:$CLASSPATH" org.antlr.v4.Tool'
```

4. Install python runtime:

```bash
pip install antlr4-python3-runtime
```

## Generate ANTLR files

Whenever you make changes to `AssetSelection.g4`, the ANTLR files need to be regenerated to reflect those changes. To generate the files, under run

```bash
$ make generate
```

This will generate the following files from the `AssetSelection.g4` grammar file in a `generated` folder:

- `AssetSelection.interp`
- `AssetSelection.tokens`
- `AssetSelectionLexer.interp`
- `AssetSelectionLexer.py`
- `AssetSelectionLexer.tokens`
- `AssetSelectionListener.py`
- `AssetSelectionParser.py`
- `AssetSelectionVisitor.py`

## Adding a new `attributeExpr` alternative

When you add a new labeled alternative under the `attributeExpr` rule in `AssetSelection.g4` (e.g. `# FooAttributeExpr`):

1. **Backend resolution.** Add a corresponding `AssetSelection` subclass in `python_modules/dagster/dagster/_core/definitions/asset_selection.py`. If the new selection can be resolved against a `BaseAssetGraph` alone, implement `resolve_inner`. If it requires runtime state (materialization status, column metadata, automation registrations, etc.) and cannot be resolved against the asset graph, leave `resolve_inner` raising `NotImplementedError` — this signals to consumers that the selection must be pre-resolved before being sent to the backend.

2. **Frontend grammar.** Regenerate the JS parser via `js_modules/ui-core` (see `src/scripts/generateAssetSelection.ts`). Add `visit<Foo>AttributeExpr` handlers in:
   - `ui-core/src/shared/asset-selection/AntlrAssetSelectionVisitor.ts` (client-side evaluation)
   - `ui-core/src/asset-selection/AssetSelectionSupplementaryDataVisitor.tsx` (if it needs out-of-band data, e.g. an asset→automation map)
   - `ui-core/src/shared/asset-selection/input/useAssetSelectionAutoCompleteProvider.tsx` (autocomplete)

3. **Backend-supported allowlist (CRITICAL).** Update `dagster-cloud/js_modules/app-cloud/src/asset-selection/BackendUnsupportedSelectionVisitor.tsx`:
   - If the new filter's `resolve_inner` is implemented and works against the workspace asset graph, add its generated `<Foo>AttributeExprContext` to `BACKEND_SUPPORTED_ATTRIBUTE_EXPR_TYPES`.
   - If it raises `NotImplementedError`, leave the allowlist alone — the new filter will automatically fall back to client-side resolution with `assetKeys` passed to the Insights backend.
   - Add a test case to `__tests__/BackendUnsupportedSelectionVisitor.test.ts` under either `supported filters` or `unsupported filters`.

   The allowlist is the source of truth for which filters can be sent to the Insights / reporting backend as a selection string. New alternatives default to "unsupported" — this is intentional, so forgetting step 3 is safe: Insights still works, it just pre-resolves the selection client-side.
