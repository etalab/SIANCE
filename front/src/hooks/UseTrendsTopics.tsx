import useSWR from "swr";

import conf from "../config.json";

import { fetchWithTokenPost, fetchWithToken } from "../api/Api";

const useHighlightTopics = () => {
  return useSWR<string[]>([`${conf.api.url}/trends/topics/highlight`], (url) =>
    fetchWithToken(url) 
  )
}


const useTrendsTopics = (
  subcategories: Set<string>,
  sectors: Set<string>
) => {
  return useSWR<any>([`${conf.api.url}/trends/topics`, subcategories, sectors], (url, subcategories, sectors) =>
    fetchWithTokenPost(url, {
      subcategories:Array.from(subcategories), 
      sectors:Array.from(sectors)
    })
  );
};

export { useHighlightTopics }
export default useTrendsTopics;
