import React from "react";

import { useHistogramScales } from "./HistogramScales";
import { Positionned, Datum } from "./Types";

type HistogramTooltipProps = {
  pt: Datum;
  simple: boolean;
} & Positionned;

export default function HistogramTooltip({
  pt,
  x,
  y,
  simple,
}: HistogramTooltipProps) {
  const {
    scaleTime: xscale,
    scaleDocs: yscale,
    unit,
    bandwidth,
  } = useHistogramScales();

  const [ystart, yend] = yscale.range();
  const [xstart, xend] = xscale.range();
  const ypos = (ystart - yend) / 11;
  const xvalue = xscale(pt.key) || 0;
  const isLeft = xvalue < Math.abs(xend - xstart) / 2;
  const year = pt.key.getFullYear();
  const quarter = Math.floor(pt.key.getMonth() / 3) + 1;

  const showUnit = pt.value === 1 ? unit : `${unit}s`;

  return (
    <g transform={`translate(${x + xvalue + bandwidth / 2},${y})`}>
      <line
        x1={0}
        y1={ystart}
        x2={0}
        y2={yend - 10}
        stroke="black"
        strokeWidth={1}
      />
      {simple ? null : (
        <>
          <text
            x={isLeft ? +5 : -5}
            y={ypos - 10}
            textAnchor={isLeft ? "start" : "end"}
          >
            {year} trimestre {quarter}
          </text>
          <text
            x={isLeft ? +5 : -5}
            y={ypos + 10}
            textAnchor={isLeft ? "start" : "end"}
          >
            {pt.value} {showUnit}
          </text>
        </>
      )}
    </g>
  );
}
