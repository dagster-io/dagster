import {Box} from '@dagster-io/ui-components';

import {EvaluationConditionalLabel} from '../EvaluationConditionalLabel';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/EvaluationConditionalLabel',
  component: EvaluationConditionalLabel,
};

export const Default = () => {
  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <EvaluationConditionalLabel segments={['Hello']} />
      <EvaluationConditionalLabel segments={['(foo OR bar)']} />
      <EvaluationConditionalLabel segments={['(foo OR bar)', 'AND', '(baz OR derp)']} />
      <EvaluationConditionalLabel segments={['(foo OR bar)', 'SINCE', '(baz OR derp)']} />
      <EvaluationConditionalLabel segments={['NOT', '(baz OR derp)']} />
    </Box>
  );
};
