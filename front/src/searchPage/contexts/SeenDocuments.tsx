import React from "react";

import constate from "constate";

import { SeenLetters, ReduceSeenLettersAction } from "../Types";

const defaultSeenLetters: SeenLetters = new Set();

function reduceSeenLetters(
  old: SeenLetters,
  action: ReduceSeenLettersAction
): SeenLetters {
  switch (action.type) {
    case "del":
      const newset = new Set(old);
      newset.delete(action.value);
      return newset;
    case "add":
      return new Set(old).add(action.value);
    default:
      return old;
  }
}

function init(d: SeenLetters) {
  if (window.localStorage.getItem("seen-letters")) {
    return new Set<number>(
      JSON.parse(window.localStorage.getItem("seen-letters") || "[]")
    );
  } else {
    return d;
  }
}

const [SeenLettersProvider, useSeenLetters, useDispatchSeenLetters] = constate(
  () => {
    const result = React.useReducer(
      reduceSeenLetters,
      defaultSeenLetters,
      init
    );
    const seenLetters = result[0];
    React.useEffect(() => {
      window.localStorage.setItem(
        "seen-letters",
        JSON.stringify(Array.from(seenLetters))
      );
    }, [seenLetters]);
    return result;
  },
  (v) => v[0],
  (v) => v[1]
) as [
  React.FC<any>,
  () => SeenLetters,
  () => React.Dispatch<ReduceSeenLettersAction>
];

function useIsFresh(id: number): boolean {
  const letters = useSeenLetters();
  return !letters.has(id);
}

export default useSeenLetters;
export { SeenLettersProvider, useDispatchSeenLetters, useIsFresh };
