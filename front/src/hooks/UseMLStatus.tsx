import useSWR from "swr";

import conf from "../config.json";
import { fetchWithToken } from "../api/Api";

export type MLStatus = {
  total_letters: number;
  total_annotations: number;
  total_annotated_letters: number;
  total_predictions: number;
};

const useMLStatus = () => {
  return useSWR<MLStatus>(`${conf.api.url}/admin/ml_status`, (url) =>
    fetchWithToken(url)
  );
};

export default useMLStatus;
