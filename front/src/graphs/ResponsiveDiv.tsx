import React from "react";

export const ResponsiveDims = React.createContext<[number, number]>([600, 300]);

const ResponsiveDiv: React.FunctionComponent<{}> = ({ children }) => {
  const ref = React.useRef<HTMLDivElement | null>(null);
  const [sizes, setSizes] = React.useState<[number, number] | undefined>(
    undefined
  );

  const cur = ref.current;

  const fetchDims = React.useCallback(() => {
    if (cur) {
      const rect = cur.getBoundingClientRect();
      setSizes([rect.width, rect.height]);
    }
  }, [cur]);

  React.useEffect(() => {
    window.addEventListener("resize", fetchDims);
    return () => {
      window.removeEventListener("resize", fetchDims);
    };
  }, [cur, fetchDims]);

  return (
    <div
      ref={(node) => {
        if (node && ref.current === null) {
          ref.current = node;
          const rect = node.getBoundingClientRect();
          setSizes([rect.width, rect.height]);
        }
      }}
      style={{ height: "100%", width: "100%" }}
    >
      {sizes !== undefined && (
        <ResponsiveDims.Provider value={sizes}>
          {children}
        </ResponsiveDims.Provider>
      )}
    </div>
  );
};
export default ResponsiveDiv;
