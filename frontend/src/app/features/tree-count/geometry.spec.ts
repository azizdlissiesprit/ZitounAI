import { boxAround, boxAt, EditableBox, medianSide } from './geometry';

describe('tree count geometry', () => {
  const boxes: EditableBox[] = [
    { x1: 0, y1: 0, x2: 100, y2: 100 },
    { x1: 40, y1: 40, x2: 60, y2: 60 },
    { x1: 200, y1: 200, x2: 230, y2: 230 },
  ];

  it('finds the smallest box under a click, or none', () => {
    expect(boxAt(boxes, 50, 50)).toBe(1);
    expect(boxAt(boxes, 10, 10)).toBe(0);
    expect(boxAt(boxes, 150, 150)).toBe(-1);
  });

  it('uses the median crown size for added trees', () => {
    expect(medianSide(boxes, 1000, 1000)).toBe(30);
    expect(medianSide([], 1000, 500)).toBe(30); // 3 % of the image
  });

  it('adds a box centered on the click, inside the image', () => {
    expect(boxAround(500, 500, 30, 1000, 1000)).toEqual({ x1: 485, y1: 485, x2: 515, y2: 515, added: true });
    expect(boxAround(2, 995, 30, 1000, 1000)).toEqual({ x1: 0, y1: 970, x2: 30, y2: 1000, added: true });
  });
});
