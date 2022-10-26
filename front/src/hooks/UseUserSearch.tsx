import React from "react";

import useSWR from "swr";

import conf from "../config.json";

import { Rechercher } from "../Pages";
import useNavigation from "../navigation/Utils";

import useSearchRequest, {
  SearchRequest,
  constraintList,
} from "../contexts/Search";

import {
  fetchWithToken,
  fetchWithTokenDelete,
  fetchWithTokenPut,
  fetchWithTokenPost,
} from "../api/Api";

export type UserStoredSearch = {
  id_stored_search: number;
  id_user: number;
  query: SearchRequest;
  name: string;
  last_seen: Date;
};

export type UserPreStoredSearch = {
  id_user: number;
  query: SearchRequest;
  name: string;
};

export type UserSavedSearch = {
  new_results: number;
  stored_search: UserStoredSearch;
};

export const useLastSearches = () => {
  return useSWR<SearchRequest[]>(`${conf.api.url}/user/last_search`, (url) =>
    fetchWithToken(url)
  );
};

const useSavedSearches = () => {
  const { goToPage } = useNavigation();

  const { data, isValidating, mutate, error } = useSWR<UserSavedSearch[]>(
    `${conf.api.url}/user/saved_search`,
    (url) => fetchWithToken(url)
  );

  const { dispatch } = useSearchRequest();

  const handleDelete = React.useCallback(
    (v: UserSavedSearch) => () => {
      fetchWithTokenDelete(
        `${conf.api.url}/user/saved_search`,
        v.stored_search
      ).then(() =>
        mutate(
          data?.filter(
            (w) =>
              w.stored_search.id_stored_search !==
              v.stored_search.id_stored_search
          )
        )
      );
    },
    [data, mutate]
  );

  const handleSave = React.useCallback((newSearch: UserPreStoredSearch) => {
    return fetchWithTokenPut(`${conf.api.url}/user/saved_search`, newSearch);
  }, []);

  const handleResearch = React.useCallback(
    (v: UserSavedSearch) => () => {
      const newSearch = { ...v.stored_search, last_seen: new Date() };
      dispatch({ type: "SET_SENTENCE", value: v.stored_search.query.sentence });
      dispatch({
        type: "SET_SORTING",
        sorting: { key: "date", order: "desc" },
      });
      constraintList.forEach((constraint) =>
        dispatch({
          type: "SET_CONSTRAINTS",
          constraintElement: {
            constraint: constraint,
            values: v.stored_search.query.filters[constraint.api],
          },
        })
      );
      goToPage(Rechercher, undefined);
      return fetchWithTokenPost(
        `${conf.api.url}/user/saved_search`,
        newSearch
      ).then(() =>
        mutate(
          data?.map((w) =>
            w.stored_search.id_stored_search === newSearch.id_stored_search
              ? { new_results: 0, stored_search: newSearch }
              : w
          )
        )
      );
    },
    [goToPage, dispatch, data, mutate]
  );

  return React.useMemo(
    () => ({
      data,
      isValidating,
      mutate,
      error,
      handleDelete,
      handleResearch,
      handleSave,
    }),
    [
      data,
      isValidating,
      mutate,
      error,
      handleDelete,
      handleResearch,
      handleSave,
    ]
  );
};

export default useSavedSearches;
