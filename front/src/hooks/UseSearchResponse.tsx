import React from "react";
import useSWR, { useSWRInfinite } from "swr";

import conf from "../config.json";
import { fetchWithTokenPost } from "../api/Api";
import useSearchRequest, {
  defaultSearchFilters,
  SearchRequest,
  ConstraintType,
} from "../contexts/Search";
import { ELetter } from "../models/Letter";
import { EDemand } from "../models/Demand";

const PAGE_SIZE = conf.elasticsearch.page_size;

export type SearchResult<T> = {
  doc_id: number;
  highlight: string[];
  _source: T;
  _score: number;
};

export type Result<T> = {
  total: number;
  hits: SearchResult<T>[];
};

export type LettersResult = Result<ELetter>;
export type DemandsResult = Result<EDemand>;

export function computeInfiniteStatus<T>(
  searchError: any,
  isValidating: boolean,
  undefinedSearchResult: Result<T>[] | undefined,
  searchResult: Result<T>[] | undefined,
  size: number
): {
  totalResult: number;
  displayedResults: number;
  isRefreshing: boolean;
  isReachingEnd: boolean;
  isEmpty: boolean;
  isLoadingInitialData: boolean;
  isLoadingMore: boolean;
} {
  const isLoadingInitialData =
    (!undefinedSearchResult && !searchError) || false;
  const isLoadingMore =
    isLoadingInitialData ||
    (size > 0 &&
      undefinedSearchResult &&
      typeof undefinedSearchResult[size - 1] === "undefined") ||
    false;
  const isEmpty = undefinedSearchResult?.[0]?.hits?.length === 0 || false;
  const isReachingEnd =
    isEmpty ||
    (undefinedSearchResult &&
      undefinedSearchResult[undefinedSearchResult.length - 1].hits?.length <
        PAGE_SIZE) ||
    false;
  const isRefreshing =
    (isValidating &&
      undefinedSearchResult &&
      undefinedSearchResult.length === size) ||
    false;

  const totalResult =
    (searchResult && searchResult[0] && searchResult[0].total) || 0;

  const displayedResults =
    (searchResult &&
      searchResult.length &&
      searchResult.length > 0 &&
      searchResult
        .map((page: Result<T>) => page.hits.length)
        .reduce((a, b) => a + b, 0)) ||
    0;

  return {
    totalResult,
    displayedResults,
    isRefreshing,
    isReachingEnd,
    isEmpty,
    isLoadingInitialData,
    isLoadingMore,
  };
}

/// Real Hooks

export const useCurrentInfiniteSearchResponse = <T extends {}>(
  mode: number
) => {
  const request = useSearchRequest();
  return useInfiniteSearchResponse<T>(mode, request);
};

export const useInfiniteSearchResponse = <T extends {}>(
  mode: number,
  request: SearchRequest
) => {
  // the key function of search process, requesting ElasticSearch API
  return useSWRInfinite<Result<T>>(
    (page) => [
      `${conf.api.url}/search/${
        mode === 2 ? "demands" : "letters"
      }?page=${page}`,
      request.sentence,
      request.filters,
      request.daterange,
      request.sorting,
    ],
    (url, sentence, filters, daterange, sorting) =>
      fetchWithTokenPost(url, {
        sentence,
        filters,
        daterange,
        sorting,
      }),
    {
      errorRetryCount: 2,
      revalidateOnFocus: false,
      revalidateOnMount: true,
    }
  );
};

export const useCurrentSearchResponse = <T extends {}>(
  mode: number,
  page: number
) => {
  const request = useSearchRequest();
  return useSearchResponse<T>(mode, request, page);
};

const useSearchResponse = <T extends {}>(
  mode: number,
  request: SearchRequest,
  page: number
) => {
  return useSWR<Result<T>>(
    [
      `${conf.api.url}/search/${
        mode === 2 ? "demands" : "letters"
      }?page=${page}`,
      request.sentence,
      request.filters,
      request.daterange,
      request.sorting,
    ],
    (url, sentence, filters, daterange, sorting) =>
      fetchWithTokenPost(url, {
        sentence,
        filters,
        daterange,
        sorting,
      }),
    {
      errorRetryCount: 2,
      revalidateOnFocus: false,
      revalidateOnMount: true,
    }
  );
};

export const useLastResultsMatching = (
  constraint: ConstraintType,
  values: string[]
) => {
  const api = constraint.api;
  const request: SearchRequest = React.useMemo(
    () => ({
      daterange: [
        new Date(1970, 0, 0).getFullYear(),
        new Date().getFullYear(),
      ] as [number, number],
      sentence: "",
      sorting: { key: "date", order: "desc" },
      filters: { ...defaultSearchFilters, [api]: values },
    }),
    [api, values]
  );
  return useSearchResponse<ELetter>(1, request, 0);
};

export default useSearchResponse;
