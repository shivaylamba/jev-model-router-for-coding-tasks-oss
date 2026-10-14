export interface Page<T> {
  /** The items on this page, in their original order. */
  items: T[];
  /** The requested page number (1-based). */
  page: number;
  pageSize: number;
  totalItems: number;
  /** Number of pages needed to show every item; 0 when there are no items. */
  totalPages: number;
  /** True when a later page has items. */
  hasNext: boolean;
  /** True when page > 1 and there is at least one item. */
  hasPrev: boolean;
}

/**
 * Return one page of `items`. Pages are numbered from 1: page 1 holds the first
 * `pageSize` items, page 2 the next `pageSize`, and so on; the last page may be
 * shorter. A page past the end has no items. `items` is not modified.
 *
 * Throws RangeError when `page` or `pageSize` is not an integer >= 1.
 */
export function paginate<T>(items: readonly T[], page: number, pageSize: number): Page<T> {
  if (!Number.isInteger(page) || page < 1) throw new RangeError("page must be an integer >= 1");
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError("pageSize must be an integer >= 1");

  const totalItems = items.length;
  const totalPages = Math.ceil(totalItems / pageSize);
  const start = (page - 1) * pageSize;
  const pageItems = items.slice(start, start + pageSize);

  return {
    items: pageItems,
    page,
    pageSize,
    totalItems,
    totalPages,
    hasNext: page < totalPages,
    hasPrev: page > 1 && totalItems > 0,
  };
}
