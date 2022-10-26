import React from "react";
import * as d3array from "d3-array";
import * as d3scale from "d3-scale";

export type Datum = {
  key: string;
  value: number;
};

type LolipopProps = {
  data: Datum[];
};

export default function Lolipop({ data }: LolipopProps) {
  const width = 600;
  const height = 300;

  data.sort((a, b) => a.value - b.value);

  const vmin = 0; //d3array.min(data.map((d) => d.value))
  const vmax = d3array.max(data.map((d) => d.value)) || 5;

  const x = d3scale
    .scaleLinear()
    .domain([vmin, vmax])
    .range([20, width - 20]);
  const y = d3scale
    .scaleBand()
    .padding(1)
    .range([height - 20, 20])
    .domain(data.map((d) => d.key));

  return (
    <svg viewBox={`0 0 ${width} ${height}`} height={height} width="100%">
      <defs>
        <pattern
          id="pattern-stripe"
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)"
        >
          <rect
            width="2"
            height="4"
            transform="translate(0,0)"
            fill="orange"
          ></rect>
        </pattern>
        <filter id="halo" colorInterpolationFilters="linearRGB">
          <feGaussianBlur
            stdDeviation="3 3"
            in="SourceGraphic"
            edgeMode="none"
            result="blur1"
          />
          <feBlend
            mode="normal"
            in="blur1"
            in2="SourceGraphic"
            result="blend1"
          />
        </filter>
      </defs>
      {data.map((d) => (
        <g key={d.key} transform={`translate(0, ${y(d.key)})`}>
          <line x1={x(d.value)} x2={0} y1={0} y2={0} stroke="black" />
          <text dy={4} textAnchor="end" dx={-5}>
            {d.key.slice(0, 30)} ... {d.value} docs
          </text>
          <circle fill="teal" cx={x(d.value)} cy={0} r={7} />
        </g>
      ))}
    </svg>
  );
}
