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
