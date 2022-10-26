import fetch from "unfetch";
import conf from "../config.json";
import { useState, useEffect } from "react";
import { Annotation } from "../hooks/UseAnnotations";

// Debounces a value
// so that updates of this new "debounced"
// value is slower and respects a
// policy of updating every "delay"
export function useDebounce<T>(value: T, delay: number) {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

interface NetworkError extends Error {
  status?: number;
}

export const fetchWithToken = async (url: string) => {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("jwt-token")}`,
    },
  });
  if (response.status !== 200) {
    const err = new Error("Network error") as NetworkError;
    err.message = JSON.stringify(response);
    err.status = response.status;
    throw err;
  } else {
    return await response.json();
  }
};

export const fetchWithTokenPost = async (url: string, data: any) => {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("jwt-token")}`,
    },
    method: "POST",
    body: JSON.stringify(data),
  });
  if (response.status !== 200) {
    const err = new Error("Network Error") as NetworkError;
    err.status = response.status;
    err.message = JSON.stringify(response);
    console.log(err);
    console.log(response.status);
    console.log(response);
    throw err;
  } else {
    return await response.json();
  }
};

export const fetchWithTokenDelete = async (url: string, data: any) => {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("jwt-token")}`,
    },
    method: "DELETE",
    body: JSON.stringify(data),
  });
  if (response.status !== 200) {
    const err = new Error("Network Error") as NetworkError;
    err.status = response.status;
    err.message = JSON.stringify(response);
    console.log(err);
    console.log(response.status);
    console.log(response);
    throw err;
  } else {
    return await response.json();
  }
};

export const fetchWithTokenPut = async (url: string, data: any) => {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("jwt-token")}`,
    },
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (response.status !== 200) {
    const err = new Error("Network Error") as NetworkError;
    err.status = response.status;
    err.message = JSON.stringify(response);
    console.log(err);
    console.log(response.status);
    console.log(response);
    throw err;
  } else {
    return await response.json();
  }
};

export type authenticateResponse = {
  data?: string;
  error?: string;
};

/**
 * Sends to the server a request to log a given user
 * action.
 */
export const sendUserLog = async (action_type: string, details: string) => {
  const data = { action_type, details };
  const token = localStorage.getItem("jwt-token") || "";
  fetch(`${conf.api.url}/statistics`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
};

export const sendAnnotations = async (annotations: Annotation[]) => {
  const body = JSON.stringify({annotations: annotations});
  const token = localStorage.getItem("jwt-token") || "";
  fetch(`${conf.api.url}/annotate/annotation`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: body,
  });
}


/**
 * This function is used to validate the output
 * of an API using a custom validator function.
 * @param p The promise to build upon
 * @param v The validator function to use
 */
export async function fetchValidator<T, S>(
  p: Promise<T>,
  v: (value: unknown, errs: [string, unknown, string][]) => value is S
): Promise<S> {
  const data = await p;
  const errs: Array<[string, unknown, any | string]> = [];
  if (v(data, errs)) {
    return data;
  } else {
    const e = new Error("Network Error");
    e.message = `Response is not valid ${data} / ${errs}`;
    throw e;
  }
}
