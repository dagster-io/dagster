import rehypePrism from '@mapbox/rehype-prism';
import rehypeAddClasses from 'rehype-add-classes';
import rehypeLink from 'rehype-autolink-headings';
import rehypeSlug from 'rehype-slug';

export default [
  rehypePrism,
  rehypeSlug,
  [
    rehypeLink,
    {
      behavior: 'append',
      properties: {
        className: ['no-underline', 'group'],
        style: {scrollMarginTop: '100px'},
      },
      content: {
        type: 'element',
        tagName: 'span',
        properties: {
          className: ['ml-2', 'text-gray-200', 'hover:text-gray-800', 'hover:underline'],
        },
        children: [{type: 'text', value: '#'}],
      },
    },
  ],
  [
    rehypeAddClasses,
    {
      'h1,h2,h3,h4,h5,h6': 'scroll-margin-top',
    },
  ],
];
