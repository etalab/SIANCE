/*
Dispatch in state the values of a component
*/
import React from "react";

import constate from "constate";

import { ToggleModes, ReduceModeLetters, ReduceModeSectors, ReduceModeSort } from "../Types";

const defaultModes: ToggleModes = {
  letters: 1,
  sectors: ["REP", "LUDD", "NPX", "TSR", "ESP"],
  sortOrder: "SCORE"
};

const elasticSorting: {
  name: string;
  sort: { key: "_score" | "date"; order: "desc" | "asc" };
}[] = [
  { name: "SCORE", sort: { key: "_score", order: "desc" } },
  { name: "DATE_ASC", sort: { key: "date", order: "asc" } },
  { name: "DATE_DESC", sort: { key: "date", order: "desc" } },
];


function reduceModeLetters(
  old: ToggleModes,
  action: ReduceModeLetters
): ToggleModes {
  return action !== old["letters"] ? { ...old, letters: action } : old;
}

function reduceModeSectors(
  old: ToggleModes,
  action: ReduceModeSectors
): ToggleModes {
  return action !== old["sectors"] ? { ...old, sectors: action } : old;
}

function reduceModeSort(
  old: ToggleModes,
  action: ReduceModeSort
): ToggleModes {
  return action !== old["sortOrder"] ? { ...old, sortOrder: action } : old;
}


function constateWrapper(toggleName: "letters" | "sectors" | "sortOrder") {
  if (toggleName === "letters") {
    return constate(
      () => {
        return React.useReducer(reduceModeLetters, defaultModes);
      },
      (v) => v[0],
      (v) => v[1]
    ) as [React.FC<any>, () => {"letters": ToggleModes["letters"]}, () => React.Dispatch<ReduceModeLetters>];
      
  } if (toggleName === "sectors") {
    return constate(
      () => {
        return React.useReducer(reduceModeSectors, defaultModes);
      },
      (v) => v[0],
      (v) => v[1]
    ) as [React.FC<any>, () => {"sectors": ToggleModes["sectors"]}, () => React.Dispatch<ReduceModeSectors>];
  } else {
    return constate(
      () => {
        return React.useReducer(reduceModeSort, defaultModes);
      },
      (v) => v[0],
      (v) => v[1]
    ) as [React.FC<any>, () => {"sortOrder": ToggleModes["sortOrder"]}, () => React.Dispatch<ReduceModeSort>];
  }
}


const [ModeLettersProvider, useModeLetters, useDispatchModeLetters] = constateWrapper("letters");
const [ModeSectorsProvider, useModeSectors, useDispatchModeSectors] = constateWrapper("sectors");
const [ModeSortProvider, useModeSort, useDispatchModeSort] = constateWrapper("sortOrder");

export {
  defaultModes,
  elasticSorting,
  ModeLettersProvider,
  ModeSectorsProvider,
  ModeSortProvider,
  useModeLetters,
  useModeSectors,
  useModeSort,
  useDispatchModeLetters,
  useDispatchModeSectors,
  useDispatchModeSort
};
