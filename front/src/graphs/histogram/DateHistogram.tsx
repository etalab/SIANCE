import React from "react";

import * as d3array from "d3-array";

import HistogramScales from "./HistogramScales";
import { Positionned, Datum } from "./Types";
import HistogramCurve from "./HistogramCurve";
import { DocCountAxis, DateAxis } from "./Axis";
import HistogramOverlay from "./Overlay";
import HistogramTooltip from "./Tooltip";
import HistogramSelection from "./HistogramSelection";
import HistogramDefs from "./HistogramDefs";

import { ResponsiveDims } from "../../graphs/ResponsiveDiv";
import { makeStyles } from "@material-ui/core";

const useFullStyles = makeStyles(() => ({
  rootSvg: {
    minHeight: "160px",
  },
}));

const useSimpleStyles = makeStyles(() => ({
  rootSvg: {
    minHeight: "110px",
    overflow: "hidden",
  },
}));

function SimpleHistogram({
  width,
  height,
  data,
  setRange,
  range,
  unit,
}: {
  data: Datum[];
  setRange: (range: [number, number]) => void;
  range: [number, number];
  unit: string;
} & Positionned) {
  const styles = useSimpleStyles();

  const [localRange, setLocalRange] = React.useState<[number, number]>(range);
  const [hoverPt, setHoverPt] = React.useState<Datum | undefined>(undefined);

  React.useEffect(() => {
    setLocalRange(range);
  }, [range]);

  const [start, end] = range;
  const totalResults =
    d3array.sum(
      data.map(({ key, value }) =>
        start <= key.getFullYear() && key.getFullYear() <= end ? value : 0
      )
    ) || 0;

    const filterDuplicates = function(data: Datum[]){
      // remove the non-sense duplicated dates with one value = 0 AND one value > 0
        const datesPositiveValue = data.filter(d=>d.value > 0).map(d=>d.key.toDateString()) // parameter "key" is the date
        const maxDate = data.map(d=>d.key).reduce(function (a, b) { return a > b ? a : b; }).toDateString()
        return data.filter((d, id)=> {
          return datesPositiveValue.indexOf(d.key.toDateString()) === -1 // there is no >0 value for this date 
          ||  (datesPositiveValue.indexOf(d.key.toDateString()) > -1 && d.value > 0) // this is a positive value
          || d.key.toDateString() === maxDate // keep the last element of dates array, to close the graph with null value
        } )
    }

    data = filterDuplicates(data);

  return (
    <svg
      className={styles.rootSvg}
      width="100%"
      viewBox={`0 0 ${width} ${height}`}
      height={height}
    >
      <HistogramDefs />
      <HistogramScales
        y={0}
        x={10}
        width={width - 20}
        height={height - 20}
        data={data}
        unit={unit}
      >
        <HistogramCurve
          range={range}
          x={10}
          y={0}
          width={width}
          height={height - 20}
          data={data}
          showQuarters={false}
        />
        <DateAxis x={10} y={height - 20} width={width} height={20} />
        <HistogramSelection
          x={10}
          y={0}
          simple={true}
          total={totalResults}
          width={width - 50}
          height={height - 20}
          range={localRange}
        />
        {hoverPt && (
          <HistogramTooltip
            x={10}
            y={0}
            width={width / 4}
            height={height / 10}
            pt={hoverPt}
            simple={true}
          />
        )}
        <HistogramOverlay
          range={range}
          setRange={setRange}
          hoverPt={hoverPt}
          setHoverPt={setHoverPt}
          localRange={localRange}
          setLocalRange={setLocalRange}
          x={10}
          y={0}
          width={width}
          height={height}
          data={data}
        />
      </HistogramScales>
    </svg>
  );
}

function FullHistogram({
  width,
  height,
  data,
  setRange,
  range,
  unit,
}: {
  data: Datum[];
  setRange: (range: [number, number]) => void;
  range: [number, number];
  unit: string;
} & Positionned) {
  const styles = useFullStyles();

  const [hoverPt, setHoverPt] = React.useState<Datum | undefined>(undefined);
  const [localRange, setLocalRange] = React.useState<[number, number]>(range);

  React.useEffect(() => {
    setLocalRange(range);
  }, [range]);

  return (
    <svg
      className={styles.rootSvg}
      width="100%"
      viewBox={`0 0 ${width} ${height}`}
      height={height}
    >
      <HistogramDefs />
      <HistogramScales
        y={60}
        x={10}
        width={width - 74}
        height={height - 50}
        data={data}
        unit={unit}
      >
        <HistogramCurve
          x={60}
          y={30}
          width={width}
          height={height}
          range={range}
          data={data}
          showQuarters={true}
        />
        <DocCountAxis x={60} y={30} width={50} height={50} />
        <DateAxis x={60} y={height - 20} width={width - 60} height={20} />
        <HistogramSelection
          total={0}
          simple={false}
          x={60}
          y={30}
          width={width - 50}
          height={height - 30}
          range={localRange}
        />
        {hoverPt && (
          <HistogramTooltip
            x={60}
            y={30}
            width={width / 4}
            height={height / 10}
            pt={hoverPt}
            simple={false}
          />
        )}
        <HistogramOverlay
          range={range}
          setRange={setRange}
          hoverPt={hoverPt}
          setHoverPt={setHoverPt}
          localRange={localRange}
          setLocalRange={setLocalRange}
          x={60}
          y={30}
          width={width - 60}
          height={height - 30}
          data={data}
        />
      </HistogramScales>
    </svg>
  );
}

// const rough = require("../../../node_modules/roughjs/bundled/rough.cjs");

export type DateSelectionGraphProps = {
  data: Datum[];
  range: [number, number];
  setRange: (r: [number, number]) => void;
  unite: string;
  graphDims: SVGDims;
  simple?: boolean;
};

type Margins = {
  top: number;
  left: number;
  right: number;
  bottom: number;
};

type SVGDims = {
  width: number;
  height: number;
  margin: Margins;
};

export const defaultDims: SVGDims = {
  width: 600,
  height: 180,
  margin: {
    top: 40,
    left: 60,
    right: 20,
    bottom: 20,
  },
};

export function ResponsiveDateSelectionGraph(props: DateSelectionGraphProps) {
  const [width] = React.useContext(ResponsiveDims);
  return (
    <DateSelectionGraph {...props} graphDims={{ ...props.graphDims, width }} />
  );
}

export default function DateSelectionGraph({
  data,
  range,
  setRange,
  unite,
  graphDims,
  simple,
}: DateSelectionGraphProps) {
  const nonNullKeys = data.map(
    (datum) => new Date(datum.key).getFullYear() !== 1970 && datum.value > 0
  );

  const keyFirstNonNull = nonNullKeys.indexOf(true);
  const keyLastNonNull = nonNullKeys.lastIndexOf(true);
  const framedData = data.slice(keyFirstNonNull, keyLastNonNull + 1);

  // when having a date histogram, it is possible to have a
  // non complete year at the end. We pad this year
  // so that the users see it consistently
  const lastYearOfHistogram =
    data.length && new Date(data[data.length - 1].key).getFullYear();
  const lastMonthsOfHistogramsLastYear =
    (data.length &&
      lastYearOfHistogram &&
      data
        .slice(data.length - 4, data.length)
        .filter(
          ({ key }) => new Date(key).getFullYear() === lastYearOfHistogram
        )) ||
    [];

  if (
    lastMonthsOfHistogramsLastYear &&
    lastMonthsOfHistogramsLastYear.length !== 4
  ) {
    // we should pad
    for (let i = lastMonthsOfHistogramsLastYear.length; i < 4; i++) {
      framedData.push({
        key: new Date(lastYearOfHistogram, i * 3, 1),
        value: 0,
      });
    }
  }

  return (
    <>
      {data &&
        (simple ? (
          <SimpleHistogram
            data={framedData}
            x={0}
            y={0}
            width={graphDims.width}
            height={graphDims.height}
            setRange={setRange}
            range={range}
            unit={unite}
          />
        ) : (
          <FullHistogram
            data={framedData}
            x={0}
            y={0}
            width={graphDims.width}
            height={graphDims.height}
            setRange={setRange}
            range={range}
            unit={unite}
          />
        ))}
    </>
  );
}
