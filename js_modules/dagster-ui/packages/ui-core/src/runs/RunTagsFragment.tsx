import {gql} from '../apollo-client';

export const RUN_TAGS_FRAGMENT = gql`
  fragment RunTagsFragment on PipelineTag {
    key
    value
  }
`;
