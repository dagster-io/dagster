import {gql} from '@apollo/client';

export const EXECUTION_PLAN_TO_GRAPH_FRAGMENT = gql`
  fragment ExecutionPlanToGraphFragment on ExecutionPlan {
    steps {
      key
      kind
      inputs {
        dependsOn {
          key
          kind
        }
      }
    }
  }
`;
