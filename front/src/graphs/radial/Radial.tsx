import React from "react";

import * as d3shape from "d3-shape";
import * as d3array from "d3-array";
import * as d3scale from "d3-scale";

// RADIAL

const angleToSVG = (x: number | undefined) => (x || 0) - Math.PI / 2;
const angleToDeg = (x: number | undefined) => (angleToSVG(x) / Math.PI) * 180;
const polarToCartX = (r: number, theta: number | undefined) =>
  r * Math.cos(angleToSVG(theta));
const polarToCartY = (r: number, theta: number | undefined) =>
  r * Math.sin(angleToSVG(theta));

export type RadialAxis = {
  name: string;
  users: number;
  "25%": number;
  "50%": number;
  "75%": number;
};

export type RadialProps = {
  series: RadialAxis[];
  vprops: any;
  areas: ("25%" | "50%" | "75%" )[];
};

const radialDims = {
  width: 600,
  padding: 50,
  height: 400,
};

function Radial({ series, vprops, areas }: RadialProps) {
  const [currentCurve, setCurrentCurve] = React.useState<string>("");
  const maximalValue  = d3array.max(series.map(a => a["75%"])) || 40;
  const minimalValue = 0;

  console.log(series);
  console.log(vprops);


  const scaleTheta = d3scale
    .scaleBand()
    .align(0)
    .domain(series.map((a) => a.name))
    .range([0, 2 * Math.PI]);

  const scaleR = d3scale
    .scaleSqrt()
    .domain([minimalValue, maximalValue * 1.4])
    .range([10, radialDims.height / 2 - radialDims.padding]);

  const path = d3shape.line();
  const rpath = d3shape.lineRadial().curve(d3shape.curveCardinalClosed);

  return (
    <svg viewBox="0 0 600 400">
      <g
        transform={`translate(${radialDims.width / 2}, ${
          radialDims.height / 2
        })`}
      >
        <g>
          {scaleR.ticks(3).map((r) => (
            <React.Fragment key={r}>
              <circle
                key={r}
                opacity="0.5"
                fill="none"
                stroke="gray"
                r={scaleR(r)}
              />
            </React.Fragment>
          ))}
        </g>
        {series.map((a) => (
          <g key={a.name}>
            <path
              opacity="0.5"
              stroke="gray"
              d={
                path([
                  [0, 0],
                  [
                    polarToCartX(scaleR.range()[1] + 15, scaleTheta(a.name)),
                    polarToCartY(scaleR.range()[1] + 15, scaleTheta(a.name)),
                  ],
                ]) || undefined
              }
            />
            <g
              transform={`translate(${polarToCartX(
                scaleR.range()[1] + 10,
                scaleTheta(a.name)
              )},
              ${polarToCartY(scaleR.range()[1] + 10, scaleTheta(a.name))})`}
            >
              <g transform={`rotate(${90 + angleToDeg(scaleTheta(a.name))})`}>
                <text opacity="0.7" dx="5">
                  {a.name}
                </text>
              </g>
            </g>
          </g>
        ))}
        {areas.map((vName) => (
          <path
            key={vName}
            pointerEvents="fill"
            onMouseEnter={() => setCurrentCurve(vName)}
            onMouseLeave={() => setCurrentCurve("")}
            fill={
              vName === currentCurve ? vprops[vName]?.color || "none" : "none"
            }
            fillOpacity="0.3"
            stroke={vprops[vName]?.color}
            d={
              rpath(
                series.map((a) => [
                  scaleTheta(a.name) || 0,
                  scaleR(a[vName]) ||
                    0,
                ])
              ) || undefined
            }
          />
        ))}
        <g>
          {scaleR.ticks(3).map((r) => (
            <React.Fragment key={r}>
              <text
                x={0}
                y={(scaleR(r) || 0) + 5}
                textAnchor="middle"
                stroke="white"
                strokeWidth="4"
                fill="white"
              >
                {r}
              </text>
              <text
                opacity="0.5"
                x={0}
                y={(scaleR(r) || 0) + 5}
                textAnchor="middle"
              >
                {r}
              </text>
            </React.Fragment>
          ))}
        </g>
      </g>
    </svg>
  );
}

export default Radial;
