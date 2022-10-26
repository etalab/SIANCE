import useSWR from "swr";

import { fetchWithToken } from "../api/Api";
import conf from "../config.json";


const useThemes = () => {
  return useSWR<string[]>(
    `${conf.api.url}/export/themes`,
    (url) => fetchWithToken(url),
    {
        revalidateOnFocus: false,
        revalidateOnReconnect: false,
      }
  );
};

export default useThemes;
