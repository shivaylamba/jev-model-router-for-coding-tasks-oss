import { test } from "node:test";
import assert from "node:assert/strict";
import { ProductService, type Product } from "../src/productService.ts";

test("caches a product after the first lookup", async () => {
  let calls = 0;
  const service = new ProductService({
    async fetchProduct(id: string): Promise<Product> {
      calls += 1;
      return { id, name: `Product ${id}`, priceCents: 1000 };
    },
  });
  assert.equal((await service.getProduct("p1")).name, "Product p1");
  await service.getProduct("p1");
  assert.equal(calls, 1);
});
