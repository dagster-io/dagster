## Steps to build locally

```bash
make install
make mdx
```

To build just a file:

```bash
 sphinx-build -b mdx -E . _build sections/api/apidocs/assets.rst
```
