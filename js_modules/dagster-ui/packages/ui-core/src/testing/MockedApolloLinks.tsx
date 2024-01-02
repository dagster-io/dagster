import {GraphQLRequest} from '@apollo/client';

export interface CachedGraphQLRequest extends GraphQLRequest {
  name: string;
  filepath: string;
  repo?: string;
  workspace?: boolean;
}
