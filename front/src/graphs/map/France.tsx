import React from "react";

import { makeStyles, Typography } from "@material-ui/core";

import * as d3array from "d3-array";
import * as d3scale from "d3-scale";
import * as d3shape from "d3-shape";
import * as d3color from "d3-scale-chromatic";
import * as d3interpolate from "d3-interpolate";
import * as d3geo from "d3-geo";
import * as GeoJSON from "geojson";

import rewind from "@turf/rewind";
// import regions from "../../regions.json";
import regions from "../../regions.json";

// import { decode } from "ngeohash";

import {
  Positionned,
  LocBucket,
  MapResponse,
  RegionCodeDromCom,
  MapRegions,
  RegionCode,
  RegionGeoJSONProperties,
} from "../../hooks/UseDashboardLetters";

import useSearchRequest, { Region } from "../../contexts/Search";

import { ResponsiveDims } from "../ResponsiveDiv";

/**
 * First step is to separate
 * the json into the Metropolitan France and Drom-Com
 * while ensuring json data is properly _winded_
 */
const winded = rewind(regions as any, {
  reverse: true,
}) as d3geo.ExtendedFeatureCollection<
  d3geo.ExtendedFeature<GeoJSON.Polygon, RegionGeoJSONProperties>
>;

const geo_metropolitan = {
  ...winded,
  features: winded.features.filter((v) => v.properties.code[0] !== "0"),
} as d3geo.ExtendedFeatureCollection<
  d3geo.ExtendedFeature<GeoJSON.Polygon, RegionGeoJSONProperties>
>;

const drom_coms: RegionCodeDromCom[] = ["01", "02", "03", "04", "06"];

const useMapStyles = makeStyles(() => ({
  overlay: {
    pointerEvents: "none",
    "& *": {
      pointerEvents: "none",
    },
  },
}));

export function FranceMapResponsive(props: FranceMapProps) {
  const [width] = React.useContext(ResponsiveDims);
  return <FranceMap {...props} width={width} />;
}

// ----
//
// First of all : the different maps with the
// proper geometries !
//
// ----

const GeoScaleContext = React.createContext(
  d3geo.geoConicConformal().fitSize([100, 100], winded.features[0])
);

function MetropolitanMap({
  children,
  width,
  height,
  x,
  y,
}: {
  children: React.ReactNode;
} & Positionned) {
  const geoscale = React.useMemo(
    () => d3geo.geoConicConformal().fitSize([width, height], geo_metropolitan),
    [width, height]
  );
  return (
    <g transform={`translate(${x},${y})`}>
      <GeoScaleContext.Provider value={geoscale}>
        {children}
      </GeoScaleContext.Provider>
    </g>
  );
}

function DromComMap({
  code,
  children,
  width,
  height,
  x,
  y,
}: {
  code: RegionCodeDromCom;
  children: React.ReactNode;
} & Positionned) {
  const geoscale = React.useMemo(
    () =>
      d3geo
        .geoConicConformal()
        .fitSize(
          [width, height],
          winded.features.find((v) => v.properties.code === code) as any
        ),
    [width, height, code]
  );
  return (
    <g transform={`translate(${x},${y})`}>
      <GeoScaleContext.Provider value={geoscale}>
        {children}
      </GeoScaleContext.Provider>
    </g>
  );
}

// ---
//
// Then, the construction of the bivariate choropleth scale
//
// ---

const BiVariateChoroplethContext = React.createContext<{
  scale: (documents: number, interlocutors: number) => string;
  dticks: number[];
  iticks: number[];
}>({ scale: () => "red", dticks: [0, 1, 2], iticks: [0, 1, 2] });

function BiVariateChoropleth({
  children,
  regions,
}: {
  children: React.ReactNode;
  regions: MapRegions | undefined;
}) {
  const minInterlocutors =
    (regions &&
      d3array.min(Object.values(regions).map((v) => v.nb_interlocutors))) ||
    0;
  const maxInterlocutors =
    (regions &&
      d3array.max(Object.values(regions).map((v) => v.nb_interlocutors))) ||
    1;

  const minDocuments =
    (regions && d3array.min(Object.values(regions).map((v) => v.count))) || 0;
  const maxDocuments =
    (regions && d3array.max(Object.values(regions).map((v) => v.count))) || 3;

  const scaleDocument = d3scale
    .scaleSequential(d3color.interpolateBlues)
    .domain([minDocuments, maxDocuments]);

  const scaleInterlocutor = d3scale
    .scaleSequential(d3color.interpolateGreens)
    .domain([maxInterlocutors, minInterlocutors]);

  const scale = React.useCallback(
    (documents: number, interlocutors: number) =>
      d3interpolate.interpolateRgb(
        scaleDocument(documents) || "",
        scaleInterlocutor(interlocutors) || ""
      )(0.5),
    [scaleDocument, scaleInterlocutor]
  );

  const value = React.useMemo(
    () => ({
      scale: scale,
      dticks: [minDocuments, (minDocuments + maxDocuments) / 2, maxDocuments],
      iticks: [
        minInterlocutors,
        (minInterlocutors + maxInterlocutors) / 2,
        maxInterlocutors,
      ],
    }),
    [scale, minDocuments, maxDocuments, minInterlocutors, maxInterlocutors]
  );

  return (
    <BiVariateChoroplethContext.Provider value={value}>
      {children}
    </BiVariateChoroplethContext.Provider>
  );
}

// ----
//
// Last stop before the train to nice maps
// we need to build a legend
//
// TODO: use only min/max
// and build the full legend using only d3scales
// This is going to be much more robust to changes
//
// ----

function BiVariateLegend({ width, height, x, y }: Positionned) {
  const { scale, dticks, iticks } = React.useContext(
    BiVariateChoroplethContext
  );

  const innerWidth = width - 50;
  const innerHeight = height - 50;

  const line = d3shape.line();

  return (
    <g transform={`translate(${x + 10},${y + 10})`}>
      {dticks.map((dtick, i) => (
        <React.Fragment key={i}>
          {iticks.map((itick, j) => (
            <g
              transform={`translate(${(i * innerWidth) / 3},${
                innerHeight - ((j + 1) * innerHeight) / 3
              })`}
              key={j}
            >
              <rect
                width={innerWidth / 3}
                height={innerHeight / 3}
                fill={scale(dtick, itick)}
              />
            </g>
          ))}
        </React.Fragment>
      ))}
      <path
        markerEnd="url(#arrowhead)"
        stroke="black"
        strokeWidth={4}
        d={
          line([
            [0, innerHeight],
            [innerWidth, innerHeight],
          ]) || undefined
        }
      />
      <path
        markerEnd="url(#arrowhead)"
        stroke="black"
        strokeWidth={4}
        d={
          line([
            [0, innerHeight],
            [0, 0],
          ]) || undefined
        }
      />
      <g transform="rotate(270)">
        <text x={-innerHeight} dy={-6}>
          Interlocuteurs
        </text>
      </g>
      <text y={innerHeight} dy="1em">
        Documents
      </text>
      <circle r={3} fill="black" cx={0} cy={innerHeight} />
    </g>
  );
}

// ---
//
// Print in the correct geo coords the selected interlocutors
// as points
//
// ---

function PinLocBuckets({ buckets }: { buckets: LocBucket[] }) {
  const projection = React.useContext(GeoScaleContext);
  return (
    <g>
      {buckets.map((bucket) => {
        const [x, y] = projection(bucket.properties.point) || [0, 0];
        return (
          <circle
            cx={x}
            cy={y}
            r={2}
            fill={bucket.count === 0 ? "gray" : "red"}
          />
        );
      })}
    </g>
  );
}

// ----
//
// Now that we have not only the colorscale
// but the geo positions we can start building
// the small components
//
// TODO: use CSS classes to configure the style of the graph !
// ---

function MapRegion({
  code,
  count,
  nb_interlocutors,
  selected,
  current,
  setSelectedRegion,
  setCurrentRegion,
}: {
  code: RegionCode;
  count: number;
  nb_interlocutors: number;
  selected: boolean;
  current: boolean;
  setCurrentRegion?: (region: RegionCode | undefined) => void;
  setSelectedRegion?: (region: RegionCode) => void;
}) {
  const projection = React.useContext(GeoScaleContext);
  const path = d3geo.geoPath().projection(projection);
  const { scale: heat } = React.useContext(BiVariateChoroplethContext);
  const surface = winded.features.find((v) => v.properties.code === code);

  return (
    <path
      key={code}
      d={(surface && path(surface)) || undefined}
      stroke={selected ? "teal" : "black"}
      strokeLinejoin="round"
      strokeWidth={current || selected ? 5 : 1}
      fill={heat(count, nb_interlocutors)}
      pointerEvents="fill"
      onMouseEnter={setCurrentRegion && (() => setCurrentRegion(code))}
      onMouseDown={setSelectedRegion && (() => setSelectedRegion(code))}
      onMouseLeave={setCurrentRegion && (() => setCurrentRegion(undefined))}
    />
  );
}

type FranceMapProps = {
  width: number;
  height: number;
  data?: MapResponse;
};

function RegionInformations({
  code,
  regions,
  width,
  height,
  x,
  y,
}: {
  code: RegionCode | undefined;
  regions: MapRegions | undefined;
} & Positionned) {
  const name = winded.features.find((v) => v.properties.code === code)
    ?.properties.nom;
  const count = (regions && code && regions[code].count) || 0;
  const interlocutors =
    (regions && code && regions[code].nb_interlocutors) || 0;
  return (
    <g transform={`translate(${x},${y})`}>
      <foreignObject width={width} height={height}>
        <div>
          {code && regions && (
            <>
              <Typography variant="h5">{name}</Typography>
              <Typography variant="h5" color="secondary">
                {count} documents
              </Typography>
              <Typography variant="h5" color="primary">
                {interlocutors} interlocuteurs
              </Typography>
            </>
          )}
        </div>
      </foreignObject>
    </g>
  );
}

function MapBackground({
  data,
  width,
  height,
  x,
  y,
  setCurrentRegion,
  setSelectedRegion,
}: {
  data: MapResponse | undefined;
  setCurrentRegion?: (region: RegionCode | undefined) => void;
  setSelectedRegion?: (region: RegionCode) => void;
} & Positionned) {
  return (
    <>
      <MetropolitanMap
        width={(width * 2) / 3}
        height={(height * 2) / 3}
        x={x}
        y={y}
      >
        {geo_metropolitan.features.map((v) => (
          <MapRegion
            key={v.properties.code}
            code={v.properties.code}
            count={data ? data.regions[v.properties.code].count : 0}
            selected={false}
            current={false}
            nb_interlocutors={
              data ? data.regions[v.properties.code].nb_interlocutors : 0
            }
            setCurrentRegion={setCurrentRegion}
            setSelectedRegion={setSelectedRegion}
          />
        ))}
      </MetropolitanMap>
      {drom_coms.map((code, i) => (
        <DromComMap
          key={code}
          code={code}
          width={(width * 2) / (3 * drom_coms.length) / 2}
          height={height / 3}
          x={x + ((width * 2) / (3 * drom_coms.length)) * (i + 0.25)}
          y={y + (2 * height) / 3}
        >
          <MapRegion
            code={code}
            count={data ? data.regions[code].count : 0}
            selected={false}
            current={false}
            nb_interlocutors={data ? data.regions[code].nb_interlocutors : 0}
            setCurrentRegion={setCurrentRegion}
            setSelectedRegion={setSelectedRegion}
          />
        </DromComMap>
      ))}
    </>
  );
}

const MapBackgroundMemo = React.memo(MapBackground);

function FranceMapLayout({ width, height, data }: FranceMapProps) {
  const styles = useMapStyles();
  const { filters, dispatch } = useSearchRequest();
  const selectedRegions = filters.region.map(
    (r) =>
      regions.features.find((v) => v.properties.nom === r)?.properties?.code
  ) as RegionCode[];

  const toggleSelection = React.useCallback(
    (r: RegionCode) => {
      const region_name =
        regions.features.find((v) => v.properties.code === r)?.properties
          ?.nom || "";
      const action = filters.region.includes(region_name)
        ? "DEL_CONSTRAINT"
        : "ADD_CONSTRAINT";
      dispatch({
        type: action,
        constraintElement: {
          constraint: Region,
          values: [region_name],
        },
      });
    },
    [filters, dispatch]
  );

  const [currentRegion, setCurrentRegion] = React.useState<
    RegionCode | undefined
  >(undefined);

  return (
    <>
      <MapBackgroundMemo
        width={width}
        height={height}
        x={0}
        y={0}
        data={data}
        setCurrentRegion={setCurrentRegion}
        setSelectedRegion={toggleSelection}
      />
      <g className={styles.overlay}>
        <MetropolitanMap
          width={(width * 2) / 3}
          height={(height * 2) / 3}
          x={0}
          y={0}
        >
          {geo_metropolitan.features
            .filter(
              (v) =>
                v.properties.code === currentRegion ||
                selectedRegions.includes(v.properties.code)
            )
            .map((v) => (
              <MapRegion
                key={v.properties.code}
                code={v.properties.code}
                count={data ? data.regions[v.properties.code].count : 0}
                selected={selectedRegions.includes(v.properties.code)}
                current={currentRegion === v.properties.code}
                nb_interlocutors={
                  data ? data.regions[v.properties.code].nb_interlocutors : 0
                }
                setCurrentRegion={setCurrentRegion}
                setSelectedRegion={toggleSelection}
              />
            ))}
          {data && <PinLocBuckets buckets={data.ludd_and_rep} />}
        </MetropolitanMap>
        {drom_coms
          .map((code, i) => [code, i] as const)
          .filter(
            ([code, _]) =>
              code === currentRegion || selectedRegions.includes(code)
          )
          .map(([code, i]) => (
            <DromComMap
              key={code}
              code={code}
              width={(width * 2) / (3 * drom_coms.length) / 2}
              height={height / 3}
              x={((width * 2) / (3 * drom_coms.length)) * (i + 0.25)}
              y={(2 * height) / 3}
            >
              <MapRegion
                code={code}
                count={data ? data.regions[code].count : 0}
                selected={selectedRegions.includes(code)}
                current={currentRegion === code}
                nb_interlocutors={
                  data ? data.regions[code].nb_interlocutors : 0
                }
                setCurrentRegion={setCurrentRegion}
                setSelectedRegion={toggleSelection}
              />
            </DromComMap>
          ))}

        <RegionInformations
          x={(width * 2) / 3}
          width={width / 3}
          height={height / 2}
          y={0}
          code={currentRegion}
          regions={data?.regions}
        />
        <BiVariateLegend
          width={width / 6}
          height={height / 4}
          y={(4 * height) / 6}
          x={(width * 4) / 5}
        />
      </g>
    </>
  );
}

export default function FranceMap({ width, height, data }: FranceMapProps) {
  return (
    <svg width={width} height={height}>
      <defs>
        <marker
          id="arrowhead"
          markerWidth="3"
          markerHeight="3"
          refX="0"
          refY="1.5"
          orient="auto"
        >
          <polygon points="0 0, 3 1.5, 0 3" />
        </marker>
      </defs>
      <BiVariateChoropleth regions={data?.regions}>
        <FranceMapLayout width={width} height={height} data={data} />
      </BiVariateChoropleth>
    </svg>
  );
}
