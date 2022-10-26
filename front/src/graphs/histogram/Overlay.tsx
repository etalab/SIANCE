import React from "react";

import * as d3array from "d3-array";

import { inMonthRange } from "./Utils";
import { Positionned, Datum, Pos } from "./Types";
import { useHistogramScales } from "./HistogramScales";

const getMouse = (
  e: React.MouseEvent<Element>,
  width: number,
  height: number
): Pos => {
  const dims = e.currentTarget.getBoundingClientRect();
  const rawX = e.clientX - dims.left;
  const rawY = e.clientY - dims.top;
  const x = (rawX / dims.width) * width;
  const y = (rawY / dims.height) * height;
  return { x, y };
};

const pointsEqual = (p1: Datum | undefined, p2: Datum | undefined) => {
  return (
    (!p1 && !p2) || (p1 && p2 && p1.key === p2.key && p1.value === p2.value)
  );
};

const updateRange = ([x, y]: [number, number], z: number) => {
  return [Math.min(x, y, z), Math.max(x, y, z)] as const;
};

export type HistogramOverlayProps = {
  toDataPoint: (pos: Pos) => Datum | undefined;
  startSelect: (d: Datum) => void;
  endSelect: (d: Datum) => void;
  width: number;
  height: number;
  children: React.ReactNode;
  renderTooltip: (pt: Datum) => React.ReactNode;
  renderSelection: (r: [number, number]) => React.ReactNode;
  range: [number, number];
  setRange: (r: [number, number]) => void;
};

function HistogramOverlay({
  x,
  y,
  width,
  height,
  setHoverPt,
  hoverPt,
  data,
  range,
  localRange,
  setLocalRange,
  setRange,
}: {
  data: Datum[];
  range: [number, number];
  setRange: (r: [number, number]) => void;
  localRange: [number, number];
  setLocalRange: (r: [number, number]) => void;
  hoverPt: Datum | undefined;
  setHoverPt: (pt: Datum | undefined) => void;
} & Positionned) {
  const { bandwidth, scaleTime } = useHistogramScales();

  const [down, setDown] = React.useState<boolean>(false);

  const handleMouseMove = (e: React.MouseEvent<Element>) => {
    const mouse = getMouse(e, width, height);
    const newPt = toDataPoint(mouse);

    if (!pointsEqual(hoverPt, newPt)) {
      setHoverPt(newPt);
      if (down && newPt) {
        setLocalRange(
          updateRange(localRange, newPt.key.getFullYear()) as [number, number]
        );
      }
    }
  };

  const toDataPoint = (pt: Pos) => {
    const index = d3array
      .bisector((d: Datum) => scaleTime(d.key) || 0)
      .left(data, pt.x - bandwidth);
    const d = data[index];
    return d && inMonthRange(d.key, scaleTime, pt.x) ? d : undefined;
  };

  const handleMouseLeave = (e: React.SyntheticEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setHoverPt(undefined);
    setDown(false);
    setRange(localRange);

  };

  const handleMouseStart = (e: React.SyntheticEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDown(true);
    hoverPt &&
      setLocalRange([hoverPt.key.getFullYear(), hoverPt.key.getFullYear()]);
  };

  const handleMouseEnd = (e: React.SyntheticEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDown(false);
    setRange(localRange);
  };

  return (
    <rect
      x={x}
      y={y}
      width={width}
      height={height}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onMouseUp={handleMouseEnd}
      onMouseDown={handleMouseStart}
      fillOpacity={0}
    />
  );
}

export default HistogramOverlay;
