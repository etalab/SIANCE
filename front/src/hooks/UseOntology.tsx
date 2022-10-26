import useSWR from "swr";

import { fetchWithToken } from "../api/Api";
import conf from "../config.json";

export type OntologyMetaProperties = {
  research?: boolean;
  is_rep: boolean;
  is_npx: boolean;
  fishbone?: boolean;
  is_ludd: boolean;
  is_transverse: boolean;
};

export type OntologySubcategory = OntologyMetaProperties & {
  category: string;
  subcategory: string;
  id_label: number;
  description?: string;
  creation_date?: string;
};

export type OntologyTreeLeaf<T extends Object> = OntologySubcategory & T;
export type OntologyTreeNode<T extends Object, U extends Object> = {
  category: string;
  subcategories: OntologyTreeLeaf<U>[];
} & T;

export type OntologyTree<T extends Object, U extends Object> = OntologyTreeNode<
  T,
  U
>[];

export type OntologyItem = OntologyTreeNode<{}, {}>;

const useOntology = () => {
  return useSWR<OntologyTree<{}, {}>>(
    `${conf.api.url}/export/ontology`,
    (url) => fetchWithToken(url),
    {
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
    }
  );
};

export default useOntology;
