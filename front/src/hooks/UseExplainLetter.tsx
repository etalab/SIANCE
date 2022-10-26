import useSWR from "swr";

import { fetchWithTokenPost } from "../api/Api";
import conf from "../config.json";

const useExplainLetter = (
  sentence: string,
  letter_id: number | null | undefined
) => {
  return useSWR(
    letter_id ? [sentence, letter_id] : null,
    (sentence: string, letter_id: number) =>
      fetchWithTokenPost(
        `${conf.api.url}/explain/letter?letter_id=${letter_id}`,
        {
          sentence,
          filters: {},
        }
      )
  );
};

export default useExplainLetter;
