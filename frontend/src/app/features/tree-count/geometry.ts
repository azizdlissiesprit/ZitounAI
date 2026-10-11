/** Geometry of the manual correction, in pixels of the original image (like the boxes sent by M6). */

export interface EditableBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  /** Added by the farmer (not detected by M6). */
  added?: boolean;
}

/** Index of the box under the point (the smallest one if they overlap), or -1. */
export function boxAt(boxes: EditableBox[], x: number, y: number): number {
  let found = -1;
  let foundArea = Infinity;
  boxes.forEach((b, i) => {
    const area = (b.x2 - b.x1) * (b.y2 - b.y1);
    if (x >= b.x1 && x <= b.x2 && y >= b.y1 && y <= b.y2 && area < foundArea) {
      found = i;
      foundArea = area;
    }
  });
  return found;
}

/** Median side of the boxes (the typical crown), or 3 % of the image when there is no box yet. */
export function medianSide(boxes: EditableBox[], imageWidth: number, imageHeight: number): number {
  if (!boxes.length) return Math.max(8, 0.03 * Math.max(imageWidth, imageHeight));
  const sides = boxes.map((b) => Math.sqrt((b.x2 - b.x1) * (b.y2 - b.y1))).sort((a, b) => a - b);
  const mid = Math.floor(sides.length / 2);
  return sides.length % 2 ? sides[mid] : (sides[mid - 1] + sides[mid]) / 2;
}

/** A box of the given side centered on the point, kept inside the image. */
export function boxAround(x: number, y: number, side: number, imageWidth: number, imageHeight: number): EditableBox {
  const half = side / 2;
  const x1 = Math.min(Math.max(0, x - half), Math.max(0, imageWidth - side));
  const y1 = Math.min(Math.max(0, y - half), Math.max(0, imageHeight - side));
  return { x1, y1, x2: Math.min(imageWidth, x1 + side), y2: Math.min(imageHeight, y1 + side), added: true };
}
