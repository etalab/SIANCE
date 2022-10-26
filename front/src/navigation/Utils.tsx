import { useLocation, useHistory } from "react-router";

import Pages, { PageElement } from "../Pages";

const useNavigation = () => {
  const history = useHistory();
  const location = useLocation();
  const baseParams = new URLSearchParams(location.search);

  return {
    currentPage: Pages.find((p) => p.path === location.pathname),
    goToPage: (page: PageElement, params: URLSearchParams | undefined) => {
      params?.forEach((value, key) => baseParams.set(value, key));
      history.push(`${page.path}?${baseParams.toString()}`);
    },
  };
};

export function useQuery() {
  return new URLSearchParams(useLocation().search);
}

export default useNavigation;
