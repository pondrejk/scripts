export const ACTION = 'ACTION';

export function handleActon(key) {
  return {
    stateItem: key,
    type: ACTION,
  };
}
