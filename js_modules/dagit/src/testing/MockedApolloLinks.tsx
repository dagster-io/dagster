import {GraphQLRequest} from 'apollo-link';

export interface CachedGraphQLRequest extends GraphQLRequest {
  name: string;
  filepath: string;
  repo?: string;
  workspace?: boolean;
}
