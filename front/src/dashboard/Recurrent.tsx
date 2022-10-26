import React from "react";

import { useSWRInfinite } from "swr";

// import { DataGrid, ColDef } from "@material-ui/data-grid";

import useSearchRequest from "../contexts/Search";

import { fetchWithTokenPost } from "../api/Api";

import conf from "../config.json";
import {
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
} from "@material-ui/core";

type RecurrentItem = {
  id: string;
  count: number;
  last_seen: number;
  interlocutor_name: string;
  theme: string;
};

// const columns: ColDef[] = [
//   { field: "interlocutor_name", headerName: "Interlocuteur", width: 230 },
//   { field: "theme", headerName: "Thème", width: 330 },
//   {
//     field: "last_seen",
//     headerName: "Vu dernièrement",
//     width: 230,
//     type: "number",
//     valueFormatter: (v) =>
//       new Date(v.value as number).toLocaleString("fr-FR", {
//         year: "numeric",
//         month: "long",
//         day: "numeric",
//       }),
//   },
// ];

// function DataTable({ rows }: { rows: RecurrentItem[] }) {
//   return (
//     <div style={{ width: "100%", height: "20em" }}>
//       <DataGrid rows={rows} columns={columns} pageSize={50} />
//     </div>
//   );
// }

type RecurrentResponse = {
  response: RecurrentItem[];
  after_key?: { interlocutor_name: string; theme: string };
};

type RecurrentProps = {
  test: string;
};

function Recurrent(_: RecurrentProps) {
  const { sentence, filters, daterange } = useSearchRequest();
  const { data, size, setSize } = useSWRInfinite<RecurrentResponse>(
    (pageIndex, previousPageData) => {
      if (pageIndex === 0) {
        return [
          `${conf.api.url}/dashboard/sites`,
          sentence,
          filters,
          daterange,
        ];
      }
      if (previousPageData && previousPageData.after_key) {
        return [
          `${conf.api.url}/dashboard/sites?after_theme=${previousPageData.after_key.theme}&after_interlocutor=${previousPageData.after_key.interlocutor_name}`,
          sentence,
          filters,
          daterange,
        ];
      }
      return null;
    },
    (url, sentence, filters, daterange) =>
      fetchWithTokenPost(url, {
        sentence,
        filters,
        daterange,
      }),
    {
      errorRetryCount: 2,
      revalidateOnFocus: false,
      revalidateOnMount: true,
    }
  );

  return (
    <>
      On récupère {size} pages,{" "}
      <Button
        onClick={() => setSize(size + 1)}
        disabled={data && !data[data.length - 1].after_key}
      >
        {" "}
        en récupérer plus{" "}
      </Button>
      <List>
        {data &&
          data.map((item) => (
            <React.Fragment key={item.after_key?.interlocutor_name}>
              <Divider />
              {item.response.map((value) => (
                <ListItem key={value.id}>
                  <ListItemText
                    primary={value.interlocutor_name}
                    secondary={`Theme: ${
                      value.theme
                    }; vu dernièrement en ${new Date(
                      value.last_seen
                    ).getFullYear()}`}
                  />
                </ListItem>
              ))}
            </React.Fragment>
          ))}
      </List>
    </>
  );
}

export default Recurrent;
