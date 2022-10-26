import { SearchSuggestionsT, ConstraintType } from "../contexts/Search";
import useCompletions, { useCompletion, Completions } from "./UseCompletions";
import { 
  useLettersSuggestResponse,
  SuggestLettersResponse, 
} from "./UseSuggestResponse";

export type CombinedCompletionResult = {
  value: string;
  id?: number | string;
  count?: number;
  constraint: ConstraintType;
};

function combineCompletions(
  completions: Completions | undefined,
  suggestion: SuggestLettersResponse | undefined,
  selectedFilters: ConstraintType[]
){
  const superValues = (Object.fromEntries(
    selectedFilters.map((filter) => [filter.api, new Set()])
  ) as unknown) as SearchSuggestionsT<Set<string>>;

  if (suggestion) {
    selectedFilters.forEach((filter) => {
      suggestion[filter.api].forEach(({ value }) =>
        superValues[filter.api].add(value)
      );
    });
  }

  return selectedFilters.flatMap((filter) => [
    ...(suggestion
      ? suggestion[filter.api].map(({ value, count, id }) => ({
          constraint: filter,
          value: value,
          count: count,
          id: id,
        }))
      : []),
    ...(completions && completions[filter.api]
      ? completions[filter.api]
          .filter((x) => !superValues[filter.api].has(x.value))
          .map(({ value, count, id }) => ({
            constraint: filter,
            value: value,
            count: count,
            id: id,
          }))
      : []),
  ]);
}

export function useCombinedCompletion(
  selectedFilter: ConstraintType,
  keyword: string,
  ignoreConstraint?: boolean
): CombinedCompletionResult[] | undefined {
  // in order not to call `useCombinedCompletions` on
  const { data: rawCompletions } = useCompletion(keyword, selectedFilter);
  const { data: rawSuggestion } = useLettersSuggestResponse(ignoreConstraint);
  return combineCompletions(rawCompletions, rawSuggestion, [selectedFilter])
}

function useCombinedCompletions(
  selectedFilters: ConstraintType[],
  keyword: string,
  ignoreConstraint?: boolean
): CombinedCompletionResult[] | undefined {
  const { data: rawCompletions } = useCompletions(keyword, selectedFilters);
  const { data: rawSuggestion } = useLettersSuggestResponse(ignoreConstraint);
  return combineCompletions(rawCompletions, rawSuggestion, selectedFilters)
}

export default useCombinedCompletions;
