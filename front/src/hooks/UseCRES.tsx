import conf from "../config.json";

// import { defaultSearchFilters } from "../contexts/Search";
import { ECRES } from "../models/CRES";
import { fetchWithTokenPost } from "../api/Api";
import useSWR from "swr";

export const sampleCres: ECRES = {
  id_cres: 1000,
  name: "ENSSN-BDX-877",
  siv2: "0bL7865445678",
  id_interloctor: 1,
  summary: "coucou je suis un cres",
  natures: ["nature 1", "nature 2"],
  date: new Date(),
  inb_information: ["115", "STE3"],
  siret: "8097654567890",
  interlocutor_name: "EDF",
  site_name: "Marcoule",
};

const useCRES = (
  site_name: string[],
  id_interlocutor: number[],
  interlocutor_name: string[]
) => {
  return useSWR<ECRES[]>(
    [
      `${conf.api.url}/search/interlocutor/cres`,
      site_name,
      id_interlocutor,
      interlocutor_name,
    ],
    (
      url: string,
      site_name: string[],
      id_interlocutor: number[],
      interlocutor_name: string[]
    ) =>
      fetchWithTokenPost(url, {
        id_interlocutor: id_interlocutor || undefined,
        interlocutor_name: interlocutor_name || undefined,
        site_name: site_name || undefined,
      }),
    {
      errorRetryCount: 2,
      revalidateOnFocus: false,
      revalidateOnMount: true,
    }
  );
};

export default useCRES;
