import useSWR from "swr";

import conf from "../config.json";

import { fetchWithTokenPost } from "../api/Api";

const useTrendsThemes = (themes?: string[]) => {
    let themesFormatted = themes ? themes.map(theme => encodeURI(theme)): []
    return useSWR<any>([`${conf.api.url}/trends/themes`, themes], (url, themes) => 
        fetchWithTokenPost(url, Array.from(themesFormatted))
    )

};

export default useTrendsThemes;
