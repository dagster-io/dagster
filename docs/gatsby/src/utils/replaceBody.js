const replaceImagePath = files => (src, path) => {
  const found = files.find(({ node }) => node.absolutePath.includes(path))
  const foundPath = found.node.childImageSharp.fluid.src
  return src.replace(path, foundPath)
}

export const replaceBody = (body, allFile) => {
  return body.replace(/src="(.+)"/g, replaceImagePath(allFile.edges))
}
