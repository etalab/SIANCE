import useSWR from "swr";

import conf from "../config.json";
import { fetchWithTokenPost } from "../api/Api";
import useSearchRequest, { SearchSuggestionsT } from "../contexts/Search";
import { ConstraintType } from "../contexts/Search";

type DidYouMean = {
  text: string;
  highlighted: string;
};

export type SuggestLettersResponse = {
  dym: DidYouMean[];
  date: [Date, number][];
} & SearchSuggestionsT<{ value: string; count?: number; id?: number }[]>;

export const useLettersSuggestResponse = (ignoreContraint?: boolean | undefined) => useSuggestResponse("letters", ignoreContraint);
export const useDemandsSuggestResponse = (ignoreContraint?: boolean | undefined) => useSuggestResponse("demands", ignoreContraint);

const useSuggestResponse = (mode: "letters" | "demands", ignoreConstraint?: boolean | undefined) => {
  const { sentence, filters, daterange } = useSearchRequest();
  return useSWR<SuggestLettersResponse>(
    [`${conf.api.url}/suggestion/${mode}`, sentence, filters, daterange],
    (url, sentence, filters, daterange) =>
      fetchWithTokenPost(url, {
        sentence,
        filters: ignoreConstraint? filters:([] as ConstraintType[]),
        daterange: ignoreConstraint? daterange: [1500,3000],
      })
  );
};


export default useSuggestResponse;
