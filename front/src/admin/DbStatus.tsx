import React from "react";

import * as d3scale from "d3-scale";

import { CircularProgress } from "@material-ui/core";

import useDbStatus, { DbStatus as DbStatusType } from "../hooks/UseDbStatus";

export type DbStatusGraphProps = {
  data: DbStatusType;
};

function DbStatusGraph({ data }: DbStatusGraphProps) {
  const { total_siv2, total_letters } = data;
  const x = d3scale
    .scaleLinear()
    .domain([0, total_letters])
    .range([20, 580])
    .nice();
  const yboxes = 40;
  return (
    <svg viewBox="0 0 600 100" height="100" width="100%">
      <rect
        x={x.range()[0]}
        width={x.range()[1] - x.range()[0]}
        y={yboxes}
        height={50}
        fill="teal"
      />
      <rect
        x={x.range()[0]}
        width={x(total_siv2) || 0 - x.range()[0]}
        y={yboxes}
        height={50}
        fill="orange"
      />
      <text
        x={(x.range()[0] + (x(total_siv2) || 0)) / 2}
        y={yboxes + 50 / 2}
        dy={5}
      >
        {total_siv2}
      </text>
      <text
        x={(x.range()[1] + (x(total_siv2) || 0)) / 2}
        y={yboxes + 50 / 2}
        dy={5}
      >
        {total_letters - total_siv2}
      </text>
      <g transform={`translate(${x.range()[0]},20)`}>
        <rect width={10} height={10} y={-10} fill="orange" />
        <text textAnchor="start" dx={16}>
          Lettres avec métadonnées
        </text>
      </g>
      <g transform={`translate(${x.range()[1] / 2},20)`}>
        <rect width={10} height={10} y={-10} fill="teal" />
        <text textAnchor="start" dx={16}>
          Lettres sans métadonnées
        </text>
      </g>
    </svg>
  );
}
function DbStatus() {
  const { data } = useDbStatus();

  if (data) {
    return <DbStatusGraph data={data} />;
  } else {
    return <CircularProgress />;
  }
}

export default DbStatus;
