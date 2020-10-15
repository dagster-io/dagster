export const workspacePath = (repoName: string, repoLocation: string, path: string) => {
  const finalPath = path.startsWith('/') ? path : `/${path}`;
  return `/workspace/${repoName}@${repoLocation}${finalPath}`;
};
