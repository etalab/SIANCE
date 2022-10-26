import React from "react";

import { useHistogramScales } from "./HistogramScales";
import { Positionned } from "./Types";

import { makeStyles } from "@material-ui/core";

const useStyles = makeStyles((theme) => ({
  curveTotal: {
    color: theme.palette.secondary.contrastText,
    fontWeight: 600,
    textAnchor: "middle",
  },
}));

function HistogramSelection({
  total,
  simple,
  range,
  x,
  y,
}: Positionned & { total: number; range: [number, number]; simple: boolean }) {
  const styles = useStyles();
  const { datemin, scaleTime, scaleDocs } = useHistogramScales();

  const width =
    (scaleTime(new Date(range[1] + 1, 0)) || 0) -
    (scaleTime(new Date(Math.max(range[0], datemin.getFullYear()), 0)) || 0);
  const height = scaleDocs.range()[0] - scaleDocs.range()[1];
  const startX =
    scaleTime(new Date(Math.max(range[0], datemin.getFullYear()), 0)) || 0;
  return (
    <g transform={`translate(${x},${y})`}>
      <rect
        pointerEvents="none"
        fillOpacity={0.1}
        // fill="teal"
        stroke="gray"
        strokeDasharray="2, 5"
        width={width}
        fill="url(#pattern-stripe)"
        height={height}
        y={scaleDocs.range()[1]}
        x={startX}
      />
      {simple && (
        <text
          dx={width / 2}
          x={startX}
          y={height}
          dy={-20}
          className={styles.curveTotal}
        >
          {total}
        </text>
      )}
    </g>
  );
}

export default HistogramSelection;
