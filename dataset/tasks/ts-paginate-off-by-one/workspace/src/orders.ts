import { paginate, type Page } from "./paginate.ts";

export interface Order {
  id: number;
  customer: string;
  totalCents: number;
}

export function listOrders(orders: readonly Order[], query: { page?: string; size?: string }): Page<Order> {
  const page = query.page === undefined ? 1 : Number(query.page);
  const size = query.size === undefined ? 10 : Number(query.size);
  return paginate(orders, page, size);
}
