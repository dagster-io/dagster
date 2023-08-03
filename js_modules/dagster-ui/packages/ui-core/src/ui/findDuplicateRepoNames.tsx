export const findDuplicateRepoNames = (repoNames: string[]) => {
  const uniques = new Set<string>();
  const duplicates = new Set<string>();
  repoNames.forEach((repoName) => {
    if (uniques.has(repoName)) {
      duplicates.add(repoName);
    } else {
      uniques.add(repoName);
    }
  });
  return duplicates;
};
