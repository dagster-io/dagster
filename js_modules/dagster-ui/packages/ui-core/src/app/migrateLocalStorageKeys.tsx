export const migrateLocalStorageKeys = ({from, to}: {from: RegExp; to: string}) => {
  Object.entries(window.localStorage).forEach(([key, value]) => {
    if (from.test(key)) {
      const newKey = key.replaceAll(from, to);
      window.localStorage.setItem(newKey, value);
      window.localStorage.removeItem(key);
    }
  });
};
