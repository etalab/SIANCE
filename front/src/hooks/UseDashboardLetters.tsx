import useSWR from "swr";

import conf from "../config.json";
import useSearchRequest, { SearchRequest } from "../contexts/Search";
import { fetchWithTokenPost } from "../api/Api";
import { SuggestLettersResponse } from "../hooks/UseSuggestResponse";

export type RegionCodeDromCom =
  // DROM-COM
  "01" | "02" | "03" | "04" | "06";

export type RegionCodeMetropolitan =
  // France métropolitaine
  | "11"
  | "24"
  | "27"
  | "28"
  | "32"
  | "44"
  | "52"
  | "53"
  | "75"
  | "76"
  | "84"
  | "93"
  | "94";

export type RegionCode = RegionCodeMetropolitan | RegionCodeDromCom;

export type RegionGeoJSONProperties = {
  code: RegionCode;
  nom: string;
};

export type RegionAnalysis = {
  count: number;
};

export type RegionProperties = {
  name: string;
  code: RegionCode;
  count: number;
  nb_interlocutors: number;
};

export type LocBucket = {
  key: number;
  count: number;
  properties: {
    id_interlocutor: number;
    id_inb: number;
    point: [number, number];
    name: string;
    code_inb: number;
    site_name: string;
    cnpe_name: string;
    inb_name: string;
    inb_nature: string;
    is_seashore: boolean;
  };
};

export type MapRegions = {
  [x in RegionCode]: RegionProperties;
};

export type MapResponse = {
  ludd_and_rep: LocBucket[];
  regions: MapRegions;
};

export type DashboardResponse = {
  suggest_letters: SuggestLettersResponse;
  suggest_demands: SuggestLettersResponse;
  dashboard: MapResponse;
};

export type Positionned = {
  width: number;
  height: number;
  x: number;
  y: number;
};

export const useLettersCarto = (request: SearchRequest) => {
  return useSWR<DashboardResponse>(
    [
      `${conf.api.url}/dashboard/letters_carto`,
      request.sentence,
      request.filters,
      request.daterange,
    ],
    (url, sentence, filters, daterange) =>
      fetchWithTokenPost(url, {
        sentence,
        filters,
        daterange: daterange,
      })
  );
};

export const useHistograms = (request: SearchRequest, mode: (1|2|3)) => {

  return useSWR(
    [
      `${conf.api.url}/dashboard/histograms`,
      request.sentence,
      request.filters,
      request.daterange,
    ],
    (url, sentence, filters, daterange) =>
      fetchWithTokenPost(url, {
        sentence,
        filters,
        daterange,
      })
  );
};

export const useCurrentLettersCarto = () => {
  const request = useSearchRequest();
  return useLettersCarto(request);
};

