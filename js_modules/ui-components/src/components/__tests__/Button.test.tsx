import {render} from '@testing-library/react';

import {Button, ExternalAnchorButton, getButtonClassName} from '../Button';

describe('getButtonClassName', () => {
  it('includes iconColor class by default', () => {
    expect(getButtonClassName()).toContain('iconColor');
  });

  it('includes iconColor class when preserveIconColor is false', () => {
    expect(getButtonClassName(undefined, undefined, false)).toContain('iconColor');
  });

  it('excludes iconColor class when preserveIconColor is true', () => {
    expect(getButtonClassName(undefined, undefined, true)).not.toContain('iconColor');
  });
});

describe('Button', () => {
  it('applies iconColor class by default', async () => {
    const {findByRole} = render(<Button>Click</Button>);
    expect((await findByRole('button')).className).toContain('iconColor');
  });

  it('applies iconColor class when preserveIconColor is false', async () => {
    const {findByRole} = render(<Button preserveIconColor={false}>Click</Button>);
    expect((await findByRole('button')).className).toContain('iconColor');
  });

  it('omits iconColor class when preserveIconColor is true', async () => {
    const {findByRole} = render(<Button preserveIconColor>Click</Button>);
    expect((await findByRole('button')).className).not.toContain('iconColor');
  });
});

describe('ExternalAnchorButton', () => {
  it('applies iconColor class by default', async () => {
    const {findByRole} = render(<ExternalAnchorButton href="#">Link</ExternalAnchorButton>);
    expect((await findByRole('link')).className).toContain('iconColor');
  });

  it('applies iconColor class when preserveIconColor is false', async () => {
    const {findByRole} = render(
      <ExternalAnchorButton href="#" preserveIconColor={false}>
        Link
      </ExternalAnchorButton>,
    );
    expect((await findByRole('link')).className).toContain('iconColor');
  });

  it('omits iconColor class when preserveIconColor is true', async () => {
    const {findByRole} = render(
      <ExternalAnchorButton href="#" preserveIconColor>
        Link
      </ExternalAnchorButton>,
    );
    expect((await findByRole('link')).className).not.toContain('iconColor');
  });
});
