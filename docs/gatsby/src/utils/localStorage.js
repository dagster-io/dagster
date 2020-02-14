export function useLocalStorage(prop) {
  return {
    get: () => {
      if (typeof window === "undefined") return null;
      const item = localStorage.getItem(prop);
      if (item === "null") return null;
      return item;
    },
    set: value => {
      if (typeof window === "undefined") return null;
      return localStorage.setItem(prop, value);
    },
    remove: () => {
      if (typeof window === "undefined") return null;
      return localStorage.removeItem(prop);
    },
    clear: () => {
      if (typeof window === "undefined") return null;
      return localStorage.clear();
    }
  };
}
