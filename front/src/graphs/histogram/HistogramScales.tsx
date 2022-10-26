import React from "react";

import * as d3time from "d3-time";
import * as d3array from "d3-array";
import * as d3scale from "d3-scale";

import { Positionned, Datum } from "./Types";

import { roundToCurrYear, roundToNextYear } from "./Utils";

export const HistogramScalesContext = React.createContext({
  scaleTime: d3scale.scaleTime().domain([0, 100]).range([0, 100]).nice(),
  scaleDocs: d3scale.scaleLinear().domain([0, 100]).range([100, 0]).nice(),
  datemin: new Date(2010, 1),
  datemax: new Date(2020, 2),
  docmin: 0,
  docmax: 100,
  yearsize: 10,
  bandwidth: 3,
  unit: "lettre",
});

export const useHistogramScales = () => {
  return React.useContext(HistogramScalesContext);
};

function HistogramScales({
  width,
  height,
  data,
  children,
  unit,
}: Positionned & {
  data: Datum[];
  unit: string;
  children: React.ReactNode;
}) {
  const datemin =
    d3array.min(data.map((d) => roundToCurrYear(d.key))) ||
    d3time.timeYear.offset(roundToNextYear(new Date()), -2);

  const datemax =
    d3array.max(data.map((d) => roundToNextYear(d.key))) ||
    roundToNextYear(new Date());

  const docmin = d3array.min([...data.map((x) => x.value)]) || 0;
  const docmax = d3array.max([...data.map((x) => x.value)]) || 6;

  const scaleTime = d3scale
    .scaleTime()
    .domain([datemin, datemax])
    .range([0, width])
    .nice();

  const scaleDocs = d3scale
    .scaleSqrt()
    .domain([0, docmax])
    .range([height, 0])
    .nice();

  const yearsize =
    (scaleTime(d3time.timeYear.offset(scaleTime.domain()[0], 1)) || 0) -
    (scaleTime(scaleTime.domain()[0]) || 0);

  const bandwidth =
    (scaleTime(d3time.timeMonth.offset(scaleTime.domain()[0], 3)) || 0) -
    (scaleTime(scaleTime.domain()[0]) || 0);

  const value = React.useMemo(
    () => ({
      scaleTime,
      scaleDocs,
      yearsize,
      bandwidth,
      datemin,
      datemax,
      docmin,
      docmax,
      unit,
    }),
    [
      scaleTime,
      scaleDocs,
      yearsize,
      bandwidth,
      datemin,
      datemax,
      docmin,
      docmax,
      unit,
    ]
  );

  return (
    <HistogramScalesContext.Provider value={value}>
      {children}
    </HistogramScalesContext.Provider>
  );
}

export default HistogramScales;
