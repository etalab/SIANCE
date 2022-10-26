import useSWR from "swr";

import { fetchWithToken } from "../api/Api";
import conf from "../config.json";
import HydratedLetter from "../models/HydratedLetter";

const useHydratedLetter = (id_letter: string | number | null | undefined) => {
  return useSWR<HydratedLetter>(id_letter ? [id_letter] : null, (q) =>
    fetchWithToken(`${conf.api.url}/observe/letter?id_letter=${q}`)
  );
};

export default useHydratedLetter;
