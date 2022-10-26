import * as d3time from "d3-time";
import * as d3scale from "d3-scale";

export function roundToNextYear(d: Date): Date {
  return new Date(d.getFullYear() + 1, 0);
}

export function roundToCurrYear(d: Date): Date {
  return new Date(d.getFullYear(), 0);
}

export function inMonthRange(
  d: Date,
  xscale: d3scale.ScaleTime<number, number>,
  x: number
): boolean {
  const bandwidth =
    (xscale(d3time.timeMonth.offset(d, 3)) || 0) - (xscale(d) || 0);
  const start = xscale(d) || 0;
  const end = start + bandwidth;
  return start <= x && x <= end;
}
