import useSWR from "swr";

import conf from "../config.json";
import { fetchWithToken } from "../api/Api";

const useDownloadToken = () => {
  return useSWR<{ download_token: string }>(
    [`${conf.api.url}/download_token`],
    (url) => fetchWithToken(url),
    {
      errorRetryCount: 0,
      revalidateOnFocus: true,
      revalidateOnMount: true,
    }
  );
};

export default useDownloadToken;
