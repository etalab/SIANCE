import React from "react";
import * as d3shape from "d3-shape";
import * as d3array from "d3-array";

import { makeStyles } from "@material-ui/core";

import { useHistogramScales } from "./HistogramScales";

import { Datum, Positionned } from "./Types";

const useStyles = makeStyles((theme) => ({
  line: {
    stroke: theme.palette.secondary.dark,
    fill: theme.palette.secondary.main,
    fillOpacity: 0.3,
  },
  selectedBar: {
    fill: theme.palette.primary.main,
    transition: theme.transitions.create(["fill"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
  },
  bar: {
    fill: theme.palette.grey[300],
    transition: theme.transitions.create(["fill"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
  },
}));

type HistogramCurveProps = {
  data: Datum[];
  range: [number, number];
  showQuarters: boolean;
} & Positionned;

export default function HistogramCurve({
  data,
  x,
  y,
  width,
  height,
  range,
  showQuarters,
}: HistogramCurveProps) {
  const {
    scaleTime: xscale,
    scaleDocs: yscale,
    bandwidth,
  } = useHistogramScales();

  const [y0] = yscale.range();
  const [d0] = xscale.domain();

  const [start, end] = range;

  const styles = useStyles();

  const currentDate = new Date();

  const movingAverage: [Date, number][] = data
    .filter((value) => value.key < currentDate)
    .map((value, index) => {
      let sizeOfRange = 5;
      if (index === 0 || index === data.length - 1) {
        sizeOfRange = 3;
      } else if (index === 1 || index === data.length - 2) {
        sizeOfRange = 4;
      }

      const avg: number =
        (d3array.sum(data.slice(index - 2, index + 3), (d) => d.value) || 0) /
        sizeOfRange;
      return [new Date(value.key), avg];
    });

  const line = d3shape
    .line<[Date, number]>()
    .x((d) => (xscale(d[0]) || 0) + bandwidth / 2)
    .y((d) => yscale(d[1]) || 0)
    .curve(d3shape.curveMonotoneX);

  const curve = line([
    [d0, 0],
    ...movingAverage,
    [movingAverage[movingAverage.length - 1][0], 0],
    [d0, 0],
  ]);

  return (
    <g transform={`translate(${x},${y})`} width={width} height={height}>
      {showQuarters &&
        data.map(({ key: date, value: count }) => (
          <rect
            key={date.getTime()}
            className={
              start <= date.getFullYear() && date.getFullYear() <= end
                ? styles.selectedBar
                : styles.bar
            }
            x={xscale(date) || 0}
            y={yscale(count)}
            height={y0 - (yscale(count) || 0)}
            width={bandwidth}
          />
        ))}
      <path className={styles.line} d={curve || undefined} />
    </g>
  );
}
