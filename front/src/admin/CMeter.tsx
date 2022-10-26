import React from "react";

import * as d3shape from "d3-shape";
import * as d3scale from "d3-scale";
import { Typography } from "@material-ui/core";

const angleToSVG = (x: number | undefined) => (x || 0) - Math.PI / 2;
const angleToDeg = (x: number | undefined) => (angleToSVG(x) / Math.PI) * 180;
const polarToCartX = (r: number, theta: number | undefined) =>
  r * Math.cos(angleToSVG(theta));
const polarToCartY = (r: number, theta: number | undefined) =>
  r * Math.sin(angleToSVG(theta));

const meterDims = {
  innerRadius: 0,
  outerRadius: 200,
  width: 600,
  height: 400,
  padding: 20,
};

type NeedleProps = {
  length: number;
  buldge: number;
  angle?: number;
  dangle?: number;
  color: string;
};
function Needle({ length, buldge, angle, dangle, color }: NeedleProps) {
  const path = d3shape.line();
  const a1 = angle && dangle && angle + dangle;
  const a2 = angle && dangle && angle - dangle;
  const points: [number, number][] = [
    [0, 0],
    [polarToCartX(buldge, a2), polarToCartY(buldge, a2)],
    [polarToCartX(length, angle), polarToCartY(length, angle)],
    [polarToCartX(buldge, a1), polarToCartY(buldge, a1)],
    [0, 0],
  ];
  return <path d={path(points) || undefined} fill={color} />;
}

type MeterAreaProps = {
  startAngle: number;
  endAngle: number;
  color: string;
};

function MeterArea({ startAngle, endAngle, color }: MeterAreaProps) {
  const arc = d3shape.arc();
  return (
    <path
      d={
        arc({
          innerRadius: meterDims.innerRadius,
          outerRadius: meterDims.outerRadius,
          startAngle,
          endAngle,
        }) || undefined
      }
      fill={color}
    />
  );
}

function MeterOutline() {
  const arc = d3shape.arc();
  const path = d3shape.line();

  return (
    <>
      <path
        d={
          arc({
            innerRadius: meterDims.outerRadius - 1,
            outerRadius: meterDims.outerRadius + 1,
            startAngle: -Math.PI / 2,
            endAngle: Math.PI / 2,
          }) || undefined
        }
      />
      <path
        d={
          path([
            [-meterDims.outerRadius, 0],
            [meterDims.outerRadius, 0],
          ]) || undefined
        }
        stroke="black"
        strokeWidth={2}
      />
    </>
  );
}

type MeterLegendProps = {
  name: string;
  color: string;
};
function MeterLegend({ name, color }: MeterLegendProps) {
  return (
    <>
      <rect x={-15} y={-10} width={10} height={10} fill={color} />
      <text>{name}</text>
    </>
  );
}

export type CMeterProps = {
  maxUsers: number;
  launchUsers: number;
  monthUsers: number;
  weekUsers: number;
  text?: string;
};

function CMeter({
  maxUsers,
  launchUsers,
  monthUsers,
  weekUsers,
  text,
}: CMeterProps) {
  let margin =  Math.round(maxUsers/20);
  let angleMedium = Math.round(maxUsers/4);
  let angleHigh = Math.round(3*maxUsers/4);
  const tau = d3scale
    .scaleLinear()
    .domain([-margin, maxUsers + margin])
    .range([-Math.PI / 2, Math.PI / 2]);
  const dangle = Math.PI / 30;

  const divs = [
    {
      startAngle: tau(-margin) || 0,
      endAngle: tau(angleMedium) || 0,
      color: "#e5eddf",
    },
    {
      startAngle: tau(angleMedium) || 0,
      endAngle: tau(angleHigh) || 0,
      color: "#cedcc2",
    },
    {
      startAngle: tau(angleHigh) || 0,
      endAngle: tau(maxUsers+margin) || 0,
      color: "#a3be8c",
    },
  ];

  const needles = [
    { color: "#88c0d0", angle: tau(launchUsers), name: "Depuis le lancement" },
    { color: "#81a1c1", angle: tau(monthUsers), name: "Sur le dernier mois" },
    {
      color: "#5e81ac",
      angle: tau(weekUsers),
      name: "Sur la dernière semaine",
    },
  ];

  return (
    <svg viewBox="0 0 600 400" width="100%">
      <g transform="translate(300,300)">
        {divs.map((d) => (
          <MeterArea key={d.color} {...d} />
        ))}
        {tau.ticks().map((t) => (
          <g
            key={t}
            transform={`translate(${polarToCartX(
              meterDims.outerRadius,
              tau(t)
            )},
            ${polarToCartY(meterDims.outerRadius, tau(t))})`}
          >
            <rect
              transform={`rotate(${angleToDeg(tau(t))})`}
              x={-10}
              width={10}
              height={1}
            />
            <text
              dx={polarToCartX(15, tau(t))}
              dy={polarToCartY(15, tau(t)) + 4}
              textAnchor={
                0 <= angleToDeg(tau(t)) && angleToDeg(tau(t)) <= 60
                  ? "start"
                  : angleToDeg(tau(t)) <= 110
                  ? "middle"
                  : "end"
              }
            >
              {t}
            </text>
          </g>
        ))}
        <MeterOutline />
        {needles.map((n) => (
          <Needle
            key={n.name}
            length={meterDims.outerRadius - meterDims.padding}
            buldge={(meterDims.outerRadius - meterDims.padding) / 3}
            angle={n.angle}
            dangle={dangle}
            color={n.color}
          />
        ))}
        <circle r={4} fill="black" />
      </g>
      <g
        transform={`translate(${meterDims.width / 2 + meterDims.padding}, ${
          meterDims.height - 60
        })`}
      >
        <foreignObject width="150" height="200" y={-20} x={-200}>
          <Typography variant="button">{text}</Typography>
        </foreignObject>
        {needles.map((n, i) => (
          <g key={n.name} transform={`translate(0,${i * 20})`}>
            <MeterLegend name={n.name} color={n.color} />
          </g>
        ))}
      </g>
    </svg>
  );
}

export default CMeter;
