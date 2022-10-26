import useSWR from "swr";

import conf from "../config.json";
import { fetchWithTokenPost } from "../api/Api";
import { defaultSearchFilters } from "../contexts/Search";

const useOnTheFlyAutocomplete = (typedText: string) => {
  return useSWR<string[]>([typedText], (q) =>
    fetchWithTokenPost(`${conf.api.url}/suggestion/complete/letters`, {
      sentence: q,
      filters: defaultSearchFilters,
    })
  );
};

export default useOnTheFlyAutocomplete;
