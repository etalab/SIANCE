import React from "react";

export default function useStickyResult<T>(value: T) {
  const val = React.useRef<T>();
  if (value !== undefined) val.current = value;
  return val.current;
}
