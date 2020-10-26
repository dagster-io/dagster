import {act} from 'react-dom/test-utils';

export const asyncWait = async () => {
  await act(async () => {
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
  });
};
