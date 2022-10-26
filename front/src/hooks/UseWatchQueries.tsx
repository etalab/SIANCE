import useSWR from "swr";

import conf from "../config.json";

import { fetchWithTokenPost } from "../api/Api";
import {SearchRequestT} from "../contexts/Search";

const useWatchQueries = (
    queries: SearchRequestT<string>[],
  ) => {
    return useSWR<any>([`${conf.api.url}/watch/queries`, queries], (url, queries) =>
      fetchWithTokenPost(url, {
        queries:Array.from(queries),
      })
    );
  };

export default useWatchQueries;