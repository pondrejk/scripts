import { ACTION } from '../actions';

const initialState = {
  stateItem: [],
};

export default function mysite(state = initialState, action) {
  switch (action.type) {
    case ACTION:
      return {
        ...state,
        stateItem: action.stateItem,
      };
    default:
      return state;
  }
}
