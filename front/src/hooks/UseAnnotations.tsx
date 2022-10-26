import useSWR from "swr";
import conf from "../config.json";

import { fetchWithTokenPost } from "../api/Api";


export type Annotation = {
    id_letter: number,
    start: number,
    end: number
    sentence: string,
    category: string,
    subcategory: string,
    id_label: number,
    letter_name: string
    exploration?: boolean
}

export const useAnnotations = (category: string) => {
  return useSWR<Annotation[]>(
    [`${conf.api.url}/annotate/samples`, category],
    (url: string, c: string) =>
      fetchWithTokenPost(url, {
        category: c,
      })
  );
};

export default useAnnotations;
