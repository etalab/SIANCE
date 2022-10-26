import React from "react";

import { Location, History } from "history";
import { useHistory } from "react-router-dom";

import createValidator, { registerType } from "typecheck.macro";

import constate from "constate";

export type ConstraintType = {
  name: string;
  desc: string;
  api: keyof SearchSuggestionsT<{}>;
  boost: number;
  orientation: "THEME" | "SITE/ETABLISSEMENT" | "INSPECTION" | "SYSTEMES/SOURCES";
};

export type ConstraintElementT<T> = {
  constraint: ConstraintType;
  values: T[];
};

export type ConstraintElement = ConstraintElementT<string | number>;

export type SearchSuggestionsT<T> = {
  site_name: T;
  interlocutor_name: T;
  theme: T;
  sectors: T;
  domains: T;
  natures: T;
  paliers: T;
  resp_entity: T;
  pilot_entity: T;
  topics: T;
  equipments_trigrams: T;
  isotopes: T;
  region: T;
};

export type SearchFiltersT<T> = SearchSuggestionsT<T> & {
  id_interlocutor: number[];
  //topics: number[];
};

export type SearchRequestT<T> = {
  sentence: string;
  filters: SearchFiltersT<T>;
  daterange: [number, number];
  sorting: { key: "_score" | "date"; order: "asc" | "desc" };
};

export type SearchRequest = SearchRequestT<string[]>;

export type SearchFilters = SearchFiltersT<string[]>;
registerType("SearchRequest");
export const validateSearchRequest = createValidator<SearchRequest>();

function updateMultipleValueField(
  p: URLSearchParams,
  k: string,
  vs: string[] | number[]
): void {
  p.delete(k);
  for (const v of vs) {
    p.append(k, `${v}`);
  }
}

function updateURLFieldIfNecessary(
  p: URLSearchParams,
  k: string,
  v: number | string | string[] | number[]
) {
  if (Array.isArray(v)) {
    updateMultipleValueField(p, k, v);
  } else if (typeof v === "string") {
    p.set(k, v);
  } else {
    p.set(k, v.toString());
  }
}

const flatParameters = ["sentence"] as const;
export function updateURLWithSearchRequest(
  p: URLSearchParams,
  s: SearchRequest
) {
  Object.entries(s.filters).forEach(([key, values]) =>
    updateURLFieldIfNecessary(p, key, values)
  );
  flatParameters.forEach((key) => updateURLFieldIfNecessary(p, key, s[key]));
  updateURLFieldIfNecessary(p, "startDate", s.daterange[0]);
  updateURLFieldIfNecessary(p, "endDate", s.daterange[1]);
  updateURLFieldIfNecessary(p, "sortField", s.sorting.key);
  updateURLFieldIfNecessary(p, "sortOrder", s.sorting.order);
}

function parseSortingFromURL(
  p: URLSearchParams,
  s: SearchRequest
): { key: "_score" | "date"; order: "asc" | "desc" } {
  let key: "_score" | "date" = s.sorting.key;
  let order: "asc" | "desc" = s.sorting.order;

  switch (p.get("sortField")) {
    case "_score":
      key = "_score";
      break;
    case "date":
      key = "date";
      break;
  }

  switch (p.get("sortOrder")) {
    case "asc":
      order = "asc";
      break;
    case "desc":
      order = "desc";
      break;
  }

  return {
    key,
    order,
  };
}

function parseSearchRequestFromURL(
  p: URLSearchParams,
  s: SearchRequest
): SearchRequest {
  const filters = Object.fromEntries(
    Object.entries(s.filters).map(([k, v]) => [
      k as string,
      (p.getAll(k) || v) as string[] | number[],
    ])
  ) as SearchFilters;

  return {
    daterange: [
      parseInt(p.get("startDate") || "") || s.daterange[0],
      parseInt(p.get("endDate") || "") || s.daterange[1],
    ],
    sentence: p.get("sentence" || "") || s.sentence,
    sorting: parseSortingFromURL(p, s),
    filters: filters,
  };
}

const secondsInOneDay = 24 * 60 * 60 * 1000;

function parseSearchRequestFromLocalStorage(
  localStorageKey: string,
  s: SearchRequest
): SearchRequest {
  const currDate = new Date();
  const storeDate = new Date(
    window.localStorage.getItem(`${localStorageKey}#date`) || currDate
  );

  if (secondsInOneDay < currDate.getTime() - storeDate.getTime()) {
    window.localStorage.removeItem(localStorageKey);
    return s;
  }

  const memoryRequest = JSON.parse(
    window.localStorage.getItem(localStorageKey) || "{}"
  );

  return validateSearchRequest(memoryRequest) ? memoryRequest : s;
}

export const defaultSearchFilters = {
  site_name: [],
  interlocutor_name: [],
  theme: [],
  sectors: [],
  pilot_entity: [],
  resp_entity: [],
  topics: [],
  equipments_trigrams: [],
  isotopes: [],
  domains: [],
  natures: [],
  paliers: [],
  region: [],
  id_interlocutor: [],
} as SearchFilters;

export const InterlocutorName: ConstraintType = {
  name: "Entreprise",
  api: "interlocutor_name",
  desc: "L'entreprise ou le service à qui la lettre de suite est destinée",
  boost: 4,
  orientation: "SITE/ETABLISSEMENT",
};

export const SiteName: ConstraintType = {
  name: "Nom du site",
  api: "site_name",
  desc: "Le site inspecté",
  boost: 4,
  orientation: "SITE/ETABLISSEMENT",
};

//export const Identifiers: ConstraintType = {
//name: "SIRET/INB",
//api: "identifiers",
//desc: "Identifiants du site via numéro de SIRET ou numéro d'INB",
//boost: 4,
//};

export const Theme: ConstraintType = {
  name: "Thème",
  api: "theme",
  desc: "Le thème d'inspection corrigé pour aligner les concepts historiques",
  boost: 4,
  orientation: "THEME",
};

export const Sectors: ConstraintType = {
  name: "Secteurs",
  api: "sectors",
  desc: "Le secteur d'activité (REP, LUDD, NPX, TSR, OA, LA, ...)",
  boost: 5,
  orientation: "SITE/ETABLISSEMENT",
};

export const Domains: ConstraintType = {
  name: "Groupe de thèmes",
  api: "domains",
  desc: "Le domaine d'activité de l'établissement",
  boost: 5,
  orientation: "THEME",
};

export const Natures: ConstraintType = {
  name: "Natures",
  api: "natures",
  desc: "La nature de l'établissement",
  boost: 5,
  orientation: "SITE/ETABLISSEMENT",
};

export const Paliers: ConstraintType = {
  name: "Niveau d'enjeu, ou palier",
  api: "paliers",
  desc: "Le niveau de l'INB (palier CNPE, enjeu LUDD)",
  orientation: "SITE/ETABLISSEMENT",
  boost: 2,
};

export const ResponsibleEntity: ConstraintType = {
  name: "Entité responsable",
  api: "resp_entity",
  desc: "L'entité qui est responsable du site inspecté (division/direction)",
  boost: 2,
  orientation: "INSPECTION",
};

export const PilotEntity: ConstraintType = {
  name: "Entité pilote",
  api: "pilot_entity",
  desc: "L'entité qui est a piloté l'inspection du site (division/direction)",
  boost: 2,
  orientation: "INSPECTION",
};

export const Topics: ConstraintType = {
  name: "Catégories",
  api: "topics",
  desc: "Catégorie définie dans l'ontologie de SIANCE",
  boost: 2,
  orientation: "THEME",
};

export const EquipmentsTrigrams: ConstraintType = {
  name: "Systèmes (REP)",
  api: "equipments_trigrams",
  desc: "Systèmes détectés dans les lettres de suite",
  boost: 2,
  orientation: "SYSTEMES/SOURCES",
};

export const Isotopes: ConstraintType = {
  name: "Isotopes",
  api: "isotopes",
  desc: "Isotopes détectés dans les lettres de suite",
  boost: 2,
  orientation: "SYSTEMES/SOURCES",
};


export const Region: ConstraintType = {
  name: "Région",
  api: "region",
  desc: "Région où l'inspection a eue lieu",
  boost: 3,
  orientation: "SITE/ETABLISSEMENT",
};

export const constraintList = [
  InterlocutorName,
  SiteName,
 // Paliers,
 // Domains,
  Theme,
 // Sectors,
 // Natures,
  Topics,
  ResponsibleEntity,
 // PilotEntity,
  EquipmentsTrigrams,
  Isotopes,
 // Region,
];

export const defaultSearchRequest: SearchRequest = {
  filters: defaultSearchFilters,
  sentence: "",
  daterange: [new Date().getFullYear() - 2, new Date().getFullYear()],
  sorting: { key: "_score", order: "desc" },
};

type SearchContextType = SearchRequest & {
  dispatch: (action: ReduceAction) => void;
};

export const SearchContext = React.createContext<SearchContextType>({
  ...defaultSearchRequest,
  dispatch: () => {},
});

function mergeConstraintElement(
  s: SearchFilters,
  c: ConstraintElement,
  replace: boolean
): SearchFilters {
  const currentValues = s[c.constraint.api];
  const newRequest = {
    ...s,
    [c.constraint.api]: replace ? c.values : [...currentValues, ...c.values],
  };
  return newRequest;
}

function substractConstraint<T>(a: T[], b: T[]): T[] {
  const removables = new Set(b);
  return a.filter((x) => !removables.has(x));
}

function deleteConstraintElement(
  s: SearchFilters,
  cs: ConstraintElement
): SearchFilters {
  return Object.fromEntries(
    Object.entries(s).map(([k, v]) =>
      k === cs.constraint.api ? [k, substractConstraint(v, cs.values)] : [k, v]
    )
  ) as SearchFilters;
}

export type ReduceAction = {
  type:
    | "SET_CONSTRAINTS"
    | "ADD_CONSTRAINT"
    | "SET_SENTENCE"
    | "SET_DATE"
    | "RESET_SEARCH"
    | "RESET_FILTERS"
    | "SET_SORTING"
    | "DEL_CONSTRAINT";
  date?: [number, number];
  constraintElement?: ConstraintElement;
  constraintName?: keyof SearchFiltersT<{}>;
  value?: string;
  sorting?: { key: "_score" | "date"; order: "asc" | "desc" };
};

function reduce(old: SearchRequest, action: ReduceAction): SearchRequest {
  const year = new Date().getFullYear();
  switch (action.type) {
    case "SET_DATE":
      return action.date && action.date !== old.daterange
        ? {
            ...old,
            daterange: action.date,
          }
        : old;
    case "SET_SENTENCE":
      return action.value !== undefined
        ? {
            ...old,
            sentence: action.value,
          }
        : old;
    case "SET_CONSTRAINTS":
      return action.constraintElement
        ? {
            ...old,
            filters: {
              ...old.filters,
              [action.constraintElement.constraint.api]:
                action.constraintElement.values,
            },
          }
        : old;
    case "ADD_CONSTRAINT":
      return {
        ...old,
        filters:
          (action.constraintElement &&
            mergeConstraintElement(
              old.filters,
              action.constraintElement,
              false
            )) ||
          old.filters,
      };
    case "DEL_CONSTRAINT":
      return {
        ...old,
        filters:
          (action.constraintElement &&
            deleteConstraintElement(old.filters, action.constraintElement)) ||
          old.filters,
      };
    case "RESET_SEARCH":
      return {
        ...old,
        sentence: "",
        daterange: [year - 2, year],
        filters: defaultSearchFilters,
      };
    case "RESET_FILTERS":
      return {
        ...old,
        daterange: [year - 2, year],
        filters: defaultSearchFilters,
      };
    case "SET_SORTING":
      return action.sorting ? { ...old, sorting: action.sorting } : old;
    default:
      console.log(action);
      return old;
  }
}

function init([defaultValue, urlParams, localStorageKey]: [
  SearchRequest,
  string,
  string
]) {
  const params = new URLSearchParams(urlParams);
  const x = parseSearchRequestFromURL(
    params,
    parseSearchRequestFromLocalStorage(localStorageKey, defaultValue)
  );
  return x;
}

function save(
  localStorageKey: string,
  history: History<unknown>,
  location: Location<unknown>,
  s: SearchRequest
) {
  const currDate = new Date();
  const params = new URLSearchParams(location.search);
  updateURLWithSearchRequest(params, s);

  window.localStorage.setItem(`${localStorageKey}#date`, currDate.toString());
  window.localStorage.setItem(localStorageKey, JSON.stringify(s));

  history.push({
    ...location,
    search: params.toString(),
  });
}

const useSearchRequestState = () => {
  // const location = useLocation();
  const history = useHistory();

  const localStorageKey = "SearchRequest";

  const [inspect, dispatch] = React.useReducer(
    reduce,
    [defaultSearchRequest, history.location.search, localStorageKey] as any,
    init as any
  );

  React.useEffect(() => {
    save(localStorageKey, history, history.location, inspect);
    // WARNING: we only update based on the _searchRequest_ value
    // and may erase whatever was done by other components.
    // This only does the sync     State -----> URL / LocalStorage
    // So this is completely fine
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inspect]);

  // To prevent re-rendering and preserve
  // referential equality we _modify_ the object.
  const result = inspect as SearchRequest & {
    dispatch: React.Dispatch<ReduceAction>;
  };
  result.dispatch = dispatch;
  return result;
};

const [SearchRequestProvider, useSearchRequest] = constate(
  useSearchRequestState
) as [
  React.FC<any>,
  () => SearchRequest & { dispatch: React.Dispatch<ReduceAction> }
];

export default useSearchRequest;
export { SearchRequestProvider };
