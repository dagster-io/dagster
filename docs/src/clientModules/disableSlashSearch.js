import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

if (ExecutionEnvironment.canUseDOM) {
  document.addEventListener(
    'keydown',
    (event) => {
      if (event.key === '/' && !event.ctrlKey && !event.metaKey) {
        const activeElement = document.activeElement;

        // Check if focus is within scout-copilot element
        if (activeElement?.closest('scout-copilot')) {
          event.stopPropagation();
        }
      }
    },
    true,
  );
}
