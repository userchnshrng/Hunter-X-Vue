import type { Options } from "element-plus";

// A tall date/time panel may fit on neither side of an input in a short window.
// Allow both axes to move inside the viewport instead of clipping its footer.
export const pickerPopperOptions: Partial<Options> = {
  modifiers: [
    {
      name: "preventOverflow",
      options: {
        altAxis: true,
        tether: false,
        padding: 12,
        rootBoundary: "viewport"
      }
    }
  ]
};
