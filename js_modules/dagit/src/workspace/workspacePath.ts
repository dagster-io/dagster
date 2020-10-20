export const workspacePath = (repoName: string, repoLocation: string, path = '') => {
  const finalPath = path.startsWith('/') ? path : `/${path}`;
  return `/workspace/${repoName}@${repoLocation}${finalPath}`;
};
