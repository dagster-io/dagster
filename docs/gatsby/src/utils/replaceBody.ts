// TODO: Fix any usage

const replaceImagePath = (files: any[]) => (src: string, path: string) => {
  const found = files.find(({ node }: { node: any }) =>
    node.absolutePath.includes(path)
  );
  const foundPath = found.node.childImageSharp.fluid.src;
  return src.replace(path, foundPath);
};

export const replaceBody = (body: string, allFile: { edges: any[] }) => {
  return body.replace(/src="(.+)"/g, replaceImagePath(allFile.edges));
};
