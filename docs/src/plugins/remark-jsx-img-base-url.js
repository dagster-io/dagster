// Docusaurus prefixes `baseUrl` on markdown images, but not on JSX `<img src="/...">` in MDX.
module.exports = function remarkJsxImgBaseUrl({baseUrl}) {
  const prefix = baseUrl.replace(/\/$/, '');

  const visit = (node) => {
    if ((node.type === 'mdxJsxFlowElement' || node.type === 'mdxJsxTextElement') && node.name === 'img') {
      for (const attr of node.attributes) {
        if (
          attr.type === 'mdxJsxAttribute' &&
          attr.name === 'src' &&
          typeof attr.value === 'string' &&
          attr.value.startsWith('/') &&
          !attr.value.startsWith('//') &&
          !attr.value.startsWith(`${prefix}/`)
        ) {
          attr.value = `${prefix}${attr.value}`;
        }
      }
    }
    node.children?.forEach(visit);
  };

  return (tree) => visit(tree);
};
