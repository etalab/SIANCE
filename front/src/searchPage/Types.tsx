// import createValidator, { registerType } from "typecheck.macro";
import { SearchFiltersT } from "../contexts/Search";
import { EDemand } from "../models/Demand";
import { ELetter } from "../models/Letter";
import { SearchResult } from "../hooks/UseSearchResponse";

export type ReduceDisplayAction = {
  type:
    | "SHOW_HELP"
    | "SELECT_DATE"
    | "VIEW_LETTER"
    | "VIEW_DEMAND"
    | "SELECT_FIELD"
    | "QUIT_SELECT_FIELD"
    | "HIDE_HELP"
    | "CANCEL_DATE"
    | "QUIT_PREVIEW"
    | "SAVE_DATE"
    | "CANCEL_DATE";
  constraintName?: keyof SearchFiltersT<{}>;
  selectedLetter?: SearchResult<ELetter>;
  selectedDemand?: SearchResult<EDemand>;
};

export type InspectDisplay = {
  showHelp: boolean;
  showParasDialog: boolean;
  showDateControls: boolean;
  showFieldControls: keyof SearchFiltersT<{}> | "";
  selectedLetter?: SearchResult<ELetter>;
  selectedDemand?: SearchResult<EDemand>;
};

export type LettersDemandsMode = "letters" | "demands";

export type ToggleModes = {
  letters: 1 | 2 | 3;
  sectors: ("REP"|"LUDD"|"NPX"|"TSR"|"ESP")[];
  sortOrder: "SCORE" | "DATE_ASC" | "DATE_DESC"
};

export type ReduceModeLetters = ToggleModes["letters"];
export type ReduceModeSectors = ToggleModes["sectors"];
export type ReduceModeSort = ToggleModes["sortOrder"];

export type ReduceSeenLettersAction = { type: "add" | "del"; value: number };
export type SeenLetters = Set<number>;
