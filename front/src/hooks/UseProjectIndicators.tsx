import useSWR from "swr";

import conf from "../config.json";

import { RadialAxis } from "../graphs/radial/Radial";

import { fetchWithToken } from "../api/Api";

export type ProjectIndicators = {
  filterSeries: RadialAxis[];
  exportSeries: RadialAxis[];
  maxUsers: number;
  weekUsers: number;
  monthUsers: number;
  launchUsers: number;
  weeklyTraffic: number;
  monthlyTraffic: number;
  launchTraffic: number;
};

const useProjectIndicators = () => {
  return useSWR<ProjectIndicators>(`${conf.api.url}/admin/`, (url) =>
    fetchWithToken(url)
  );
};

export default useProjectIndicators;
