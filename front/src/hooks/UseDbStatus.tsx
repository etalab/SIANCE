import useSWR from "swr";

import conf from "../config.json";
import { fetchWithToken } from "../api/Api";

export type DbStatus = {
  total_siv2: number;
  total_letters: number;
};

const useDbStatus = () => {
  return useSWR<DbStatus>(`${conf.api.url}/admin/db_status`, (url) =>
    fetchWithToken(url)
  );
};

export default useDbStatus;
