import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {AssetNodeMenuNode, useAssetNodeMenu} from '../AssetNodeMenu';

jest.mock('../../asset-data/AssetBaseDataProvider', () => ({
  ...jest.requireActual('../../asset-data/AssetBaseDataProvider'),
  useAssetBaseData: () => ({liveData: undefined}),
}));

jest.mock('../../assets/AssetActionMenu', () => ({
  useExecuteAssetMenuItem: () => ({executeItem: null, launchpadElement: null}),
}));

const node: AssetNodeMenuNode = {
  id: '["my_schema", "my/table"]',
  assetKey: {path: ['my_schema', 'my/table']},
  definition: {
    isMaterializable: true,
    isObservable: false,
    isExecutable: true,
    isPartitioned: false,
    hasMaterializePermission: true,
  },
};

const Menu = () => {
  const {menu} = useAssetNodeMenu({node});
  return <MemoryRouter>{menu}</MemoryRouter>;
};

describe('AssetNodeMenu', () => {
  it('copies the asset key token to the clipboard', async () => {
    const writeText = jest.fn();
    Object.assign(navigator, {clipboard: {writeText}});

    render(<Menu />);

    await userEvent.click(await screen.findByText('Copy asset key'));

    // Slashes within a single path component are escaped, matching the Python
    // `AssetKey.to_escaped_user_string` behavior.
    await waitFor(() => expect(writeText).toHaveBeenCalledWith('my_schema/my\\/table'));
  });
});
