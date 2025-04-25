export const TimingControls = {
  // This is kinda goofy but to allow the jest tests to test the loading from cache we use this abstraction to allow jest
  // to stop us from loading from the server immediately so that it can confirm the cached data was loaded and returned first.
  loadFromServer: (fn: () => void) => {
    fn();
  },
  handleStatusUpdate: (fn: () => void) => {
    fn();
  },
};
