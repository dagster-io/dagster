export const formatRepositoryUrl = (url: string): string => {
  try {
    const urlObj = new URL(url);
    let org, repo, tag;
    if (urlObj.host === 'github.com') {
      [, org, repo, , tag] = urlObj.pathname.split('/', 7);
    } else if (urlObj.host === 'gitlab.com') {
      [, org, repo, , , tag] = urlObj.pathname.split('/', 8);
    }
    if (org && repo && tag) {
      return `${org}/${repo}@${tag}`;
    }
  } catch (error) {
    return url;
  }
  return url;
};
