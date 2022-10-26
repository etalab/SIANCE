import useSWR from "swr";

import conf from "../config.json";
import { fetchWithTokenPost } from "../api/Api";

import { ConstraintType, SearchSuggestionsT } from "../contexts/Search";

export type CompletionResult = {
  value: string;
  count?: number;
  id?: number;
};
export type Completions = SearchSuggestionsT<CompletionResult[]>;

export const useCompletion = (value: string, selectedFilter: ConstraintType) => {
  return useSWR<Completions>(
    [value, selectedFilter],
    (q, filter: ConstraintType) =>
      fetchWithTokenPost(`${conf.api.url}/suggestion/field_values`, {
        value: q,
        fields: [filter.api],
      })
  );
};


const useCompletions = (value: string, selectedFilters: ConstraintType[]) => {
  return useSWR<Completions>(
    [value, selectedFilters],
    (q, filters: ConstraintType[]) =>
      fetchWithTokenPost(`${conf.api.url}/suggestion/field_values`, {
        value: q,
        fields: filters.map((f) => f.api),
      })
  );
};

export default useCompletions;
