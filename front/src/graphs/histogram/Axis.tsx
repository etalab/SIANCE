import React from "react";

import { Positionned } from "./Types";
import { useHistogramScales } from "./HistogramScales";

import * as d3shape from "d3-shape";
import * as d3time from "d3-time";

export function DocCountAxis({ x, y }: Positionned) {
  const { scaleDocs: scale } = useHistogramScales();
  return (
    <g transform={`translate(${x},${y})`}>
      {scale.ticks(3).map((count: number) => (
        <g key={count} transform={`translate(0, ${scale(count)})`}>
          <rect height="1" y={-0.5} width={5} x={-5} fill="black" />
          <text textAnchor="end" key={count} y="0.3em" x={-10}>
            {count}
          </text>
        </g>
      ))}
    </g>
  );
}

export function DateAxis({ x, y }: Positionned) {
  const { scaleTime: scale, yearsize } = useHistogramScales();

  const line = d3shape.line();
  const [x1, y1] = [scale.range()[0], 0];
  const [x2, y2] = [scale.range()[1], 0];
  return (
    <g transform={`translate(${x},${y})`}>
      <path
        fill="none"
        stroke="black"
        d={
          line([
            [x1, y1],
            [x2, y2],
          ]) || undefined
        }
      />
      {scale.ticks(d3time.timeYear).map((date: Date) => (
        <g key={date.getTime()} transform={`translate(${scale(date) || 0}, 0)`}>
          <rect fill="black" width={1} height={10} y={-5} x={-0.5} />
        </g>
      ))}
      {scale
        .ticks(d3time.timeYear)
        .filter(
          (_, index, a) =>
            index !== a.length - 1 &&
            (a.length < 8 ||
              (index % Math.floor(a.length / 4) === 0 &&
                index + 3 < a.length) ||
              index === a.length - 2)
        )
        .map((date: Date) => (
          <g
            key={date.getTime()}
            transform={`translate(${scale(date) || 0}, 0)`}
          >
            <text
              textAnchor="middle"
              x={yearsize / 2}
              y={20}
              key={date.getTime()}
            >
              {date.getFullYear()}
            </text>
          </g>
        ))}
    </g>
  );
}
