import Pipelines from "./Pipelines";
import { ClientStateConfig } from "apollo-link-state";
import { InMemoryCache } from "apollo-boost";

const AppClientState: ClientStateConfig = {
  resolvers: {
    Query: {
      type(
        parent: any,
        args: { pipelineName: string; typePath: string },
        {
          cache,
          getCacheKey
        }: { cache: InMemoryCache; getCacheKey: (object: any) => string }
      ) {
        const id = getCacheKey({
          __typename: "Pipeline",
          name: args.pipelineName
        });
        const pipeline = cache.readFragment({
          id,
          fragment: Pipelines.fragments.PipelinesFragment,
          fragmentName: "PipelinesFragment"
        });
        // I'll rewrite that, this is not how it should work.
        // What I want is a path that's basicalyl
        // 'context|solid.typeName.typeName'. But the idea is roughly the same.
        const pathElements = args.typePath.split(".");
        let object: any = pipeline;
        while (pathElements.length > 0) {
          const next: any = pathElements.shift();
          if (object == null) {
            return null;
          } else if (Array.isArray(object)) {
            object = object.find(o => o.name === next);
          } else {
            object = object[next];
          }
        }
        return object;
      }
    }
  }
};

export default AppClientState;
