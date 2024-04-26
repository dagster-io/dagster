import {
  ComponentProps,
  ReactNode,
  Suspense,
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
  useMemo,
} from 'react';

// Context to store the active suspense count and a method to manipulate it
const TrackedSuspenseContext = createContext({
  useBoundary: (_id: string) => {
    return {
      onFallbackRendered: () => {
        return () => {};
      },
      onContentRendered: () => {
        return () => {};
      },
    };
  },
});

export type Boundary = {
  id: string;
  name: string;
};

export const TrackedSuspenseProvider = ({
  children,
  onContentRendered,
  onContentRemoved,
  onFallbackRendered,
  onFallbackRemoved,
}: {
  children: ReactNode;
  onContentRendered: (boundary: Boundary) => void;
  onContentRemoved: (boundary: Boundary) => void;
  onFallbackRendered: (boundary: Boundary) => void;
  onFallbackRemoved: (boundary: Boundary) => void;
}) => {
  const useBoundary = useCallback(
    (name: string) => {
      // eslint-disable-next-line react-hooks/rules-of-hooks
      const boundary: Boundary = useMemo(() => ({name, id: uniqueId()}), [name]);

      return {
        onFallbackRendered: () => {
          onFallbackRendered(boundary);
          return () => {
            onFallbackRemoved(boundary);
          };
        },
        onContentRendered: () => {
          onContentRendered(boundary);
          return () => {
            onContentRemoved(boundary);
          };
        },
      };
    },
    [onContentRemoved, onContentRendered, onFallbackRemoved, onFallbackRendered],
  );

  return (
    <TrackedSuspenseContext.Provider value={useMemo(() => ({useBoundary}), [useBoundary])}>
      {children}
    </TrackedSuspenseContext.Provider>
  );
};

export const TrackedSuspense = (props: ComponentProps<typeof Suspense> & {id: string}) => {
  const {useBoundary} = useContext(TrackedSuspenseContext);
  const boundary = useBoundary(props.id);
  return (
    <Suspense
      {...props}
      fallback={<OnRendered onRendered={boundary.onFallbackRendered}>{props.fallback}</OnRendered>}
    >
      <OnRendered onRendered={boundary.onContentRendered}>{props.children}</OnRendered>
    </Suspense>
  );
};
const OnRendered = ({
  onRendered,
  children,
}: {
  children: React.ReactNode;
  onRendered: () => () => void;
}) => {
  useLayoutEffect(onRendered, [onRendered]);
  return children;
};

let id = 0;
function uniqueId() {
  return `boundaryId${id++}`;
}
