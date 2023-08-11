type Input = {
  from: RegExp;
  to: string;
  deleteExisting?: boolean;
};

export const migrateLocalStorageKeys = ({from, to, deleteExisting = false}: Input) => {
  Object.entries(window.localStorage).forEach(([key, value]) => {
    if (from.test(key)) {
      const newKey = key.replaceAll(from, to);

      // If the new key doesn't exist yet, write it.
      if (window.localStorage.getItem(newKey) === null) {
        try {
          window.localStorage.setItem(newKey, value);
        } catch (e) {
          // Failed to write. Probably a QuotaExceededError.
        }
      }

      if (deleteExisting) {
        window.localStorage.removeItem(key);
      }
    }
  });
};
