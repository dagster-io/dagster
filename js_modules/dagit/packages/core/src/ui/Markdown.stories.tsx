import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Markdown} from './Markdown';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Markdown',
  component: Markdown,
} as Meta;

export const Simple = () => {
  return (
    <Markdown>
      {`### Hello world

[Go to zombo.com](https://zombo.com)

## Shopping list
- Milk
- Eggs
- Sugar`}
    </Markdown>
  );
};

export const MarkdownWithPython = () => {
  return (
    <Markdown>
      {`Here's my code

\`\`\`python
@asset
def continent_stats(country_stats: DataFrame, change_model: Regression) -> DataFrame:
    result = country_stats.groupby("continent").sum()
    result["pop_change_factor"] = change_model.coef_
    return result
\`\`\`
`}
    </Markdown>
  );
};

export const MarkdownWithBash = () => {
  return (
    <Markdown>
      {`Here's my code

\`\`\`bash
valid=true
count=1
while [ $valid ]
  do
    echo $count
if [ $count -eq 5 ];
then
  break
fi
  ((count++))
done
\`\`\`
`}
    </Markdown>
  );
};

export const MarkdownWithJS = () => {
  return (
    <Markdown>
      {`Here's my code

\`\`\`ts
export const foo = (): number => {
  return Infinity;
}
\`\`\`
`}
    </Markdown>
  );
};
