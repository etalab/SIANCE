import React from "react";

function HistogramDefs() {
  return (
    <defs>
      <pattern
        id="pattern-stripe"
        width="4"
        height="4"
        patternUnits="userSpaceOnUse"
        patternTransform="rotate(45)"
      >
        <rect
          width="2"
          height="4"
          transform="translate(0,0)"
          fill="black"
        ></rect>
      </pattern>
      <filter
        id="halo"
        x="-40%"
        y="-40%"
        width="180%"
        height="180%"
        filterUnits="objectBoundingBox"
        primitiveUnits="userSpaceOnUse"
        colorInterpolationFilters="linearRGB"
      >
        <feGaussianBlur
          stdDeviation="3 3"
          x="0%"
          y="0%"
          width="100%"
          height="100%"
          in="SourceGraphic"
          edgeMode="none"
          result="blur1"
        />
        <feBlend
          mode="normal"
          x="0%"
          y="0%"
          width="100%"
          height="100%"
          in="blur1"
          in2="SourceGraphic"
          result="blend1"
        />
      </filter>
      <filter id="text-background" colorInterpolationFilters="linearRGB">
        <feFlood floodColor="#FFCC99" floodOpacity="1" result="flood" />
        <feBlend mode="normal" in="SourceGraphic" in2="flood" result="blend" />
      </filter>
    </defs>
  );
}

export default HistogramDefs;
