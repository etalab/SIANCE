import React from "react";

import constate from "constate";

import { InspectDisplay, ReduceDisplayAction } from "../Types";

// import { constraintList } from "./Constraints";

const defaultInspectDisplay: InspectDisplay = {
  showHelp: true,
  showParasDialog: false,
  showDateControls: false,
  showFieldControls: "",
};

function reduceDisplayState(
  old: InspectDisplay,
  action: ReduceDisplayAction
): InspectDisplay {
  switch (action.type) {
    case "SAVE_DATE":
      return {
        ...old,
        showHelp: false,
        showDateControls: false,
        showFieldControls: "",
        showParasDialog: false,
      };
    case "SELECT_FIELD":
      return {
        ...old,
        showHelp: false,
        showDateControls: false,
        showFieldControls: action?.constraintName || old.showFieldControls,
      };
    case "SHOW_HELP":
      return {
        ...old,
        showHelp: true,
        showDateControls: false,
        showParasDialog: false,
        showFieldControls: "",
      };
    case "SELECT_DATE":
      return {
        ...old,
        showHelp: false,
        showDateControls: true,
        showParasDialog: false,
        showFieldControls: "",
      };
    case "VIEW_LETTER":
      return {
        ...old,
        showHelp: false,
        showDateControls: false,
        showFieldControls: "",
        showParasDialog: true,
        selectedLetter: action.selectedLetter || undefined,
        selectedDemand: undefined,
      };
    case "VIEW_DEMAND":
      return {
        ...old,
        showHelp: false,
        showDateControls: false,
        showFieldControls: "",
        showParasDialog: true,
        selectedDemand: action.selectedDemand || undefined,
        selectedLetter: undefined,
      };
    case "HIDE_HELP":
      return {
        ...old,
        showHelp: false,
        showDateControls: false,
        showParasDialog: false,
        showFieldControls: "",
      };
    case "CANCEL_DATE":
    case "QUIT_PREVIEW":
    case "QUIT_SELECT_FIELD":
      return {
        ...old,
        showHelp: false,
        showDateControls: false,
        showParasDialog: false,
        showFieldControls: "",
        selectedDemand: undefined,
        selectedLetter: undefined,
      };

    default:
      console.log(action);
      return old;
  }
}

function init(d: InspectDisplay) {
  if (window.localStorage.getItem("seen-date")) {
    return { ...d, showHelp: false };
  } else {
    return d;
  }
}

const [
  InspectDisplayProvider,
  useInspectDisplay,
  useInspectDispatchDisplay,
] = constate(
  () => {
    const values = React.useReducer(
      reduceDisplayState,
      defaultInspectDisplay,
      init
    );
    const help = values[0].showHelp;
    React.useEffect(() => {
      help && window.localStorage.setItem("seen-date", "true");
    }, [help]);
    return values;
  },
  (v) => {
    return v[0];
  },
  (v) => {
    return v[1];
  }
) as [
  React.FC<any>,
  () => InspectDisplay,
  () => React.Dispatch<ReduceDisplayAction>
];

export default useInspectDisplay;
export { InspectDisplayProvider, useInspectDispatchDisplay };
