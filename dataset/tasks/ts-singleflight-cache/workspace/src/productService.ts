export type Product = { id: string; name: string; priceCents: number };

export type CatalogClient = {
  fetchProduct(id: string): Promise<Product>;
};

/**
 * Product lookups with a naive cache.
 *
 * Known problems (to be fixed by moving to the async cache in
 * docs/ASYNC_CACHE.md): entries never expire, the map grows without bound,
 * and ten concurrent requests for the same product make ten API calls.
 */
export class ProductService {
  #client: CatalogClient;
  #cache = new Map<string, Product>();

  constructor(client: CatalogClient) {
    this.#client = client;
  }

  async getProduct(id: string): Promise<Product> {
    const cached = this.#cache.get(id);
    if (cached !== undefined) {
      return cached;
    }
    const product = await this.#client.fetchProduct(id);
    this.#cache.set(id, product);
    return product;
  }
}
