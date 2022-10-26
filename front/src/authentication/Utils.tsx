import React from "react";

import useSWR from "swr";

import constate from "constate";

import conf from "../config.json";

import { fetchWithToken } from "../api/Api";

type User = {
  id_user: number;
  username: string;
  fullname: string;
  is_admin: boolean;
  prefs: string;
};

type UserConfig = {
  access_token: string;
  user: User;
};

interface NetworkError extends Error {
  status?: number;
}

export type AuthError = {
  status: number;
  desc: string;
};

type AuthenticationState = {
  error: AuthError | null;
  logout: () => void;
  login: (username: string, password: string) => void;
};

export const useUserConfig = () => {
  return useSWR<UserConfig>(
    `${conf.api.url}/me`,
    (url) => {
      return fetchWithToken(url);
    },
    {
      refreshInterval: 900000,
      revalidateOnFocus: false,
      errorRetryCount: 0,
      shouldRetryOnError: false,
    }
  );
};

const useAuthentication = (): AuthenticationState => {
  const [error, setError] = React.useState<AuthError | null>(null);
  const user = useUserConfig();

  const login = React.useCallback(
    (username: string, password: string) => {
      authenticateWithCredentials(username, password).then(
        (v) => {
          localStorage.setItem("jwt-token", v.access_token);
          user.mutate(v, false);
          setError(null);
        },
        (e) => {
          console.log(e);
          localStorage.removeItem("jwt-token");
          user.mutate(null as any, false);
          setError({ status: e.status, desc: "authentication failed" });
        }
      );
    },
    [user]
  );

  React.useEffect(() => {
    if (user.error) {
      localStorage.removeItem("jwt-token");
      user.mutate(null as any, false);
    }
  }, [user, user.error, user.mutate]);

  const logout = React.useCallback(() => {
    localStorage.removeItem("jwt-token");
    user.mutate(null as any, false);
  }, [user]);

  return { error, login, logout };
};

export const [
  AuthenticationProvider,
  useUserError,
  useLogin,
  useLogout,
] = constate(
  useAuthentication,
  (v) => v.error,
  (v) => v.login,
  (v) => v.logout
) as [
  React.FC<any>,
  () => AuthError | null,
  () => (username: string, password: string) => void,
  () => () => void
];

export const authenticateWithCredentials = async (
  username: string,
  password: string
): Promise<UserConfig> => {
  const data = new URLSearchParams();
  data.append("username", username);
  data.append("password", password);

  let response;

  try {
    response = await fetch(`${conf.api.url}/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: data.toString(),
    });
  } catch (e) {
    throw new Error(`A network error occured ${e.status || null}`);
  }

  const json = await response.json();

  if (response.status !== 200) {
    const err = new Error(json?.detail || JSON.stringify(json)) as NetworkError;
    err.status = response.status;
    throw err;
  }
  return json as UserConfig;
};
