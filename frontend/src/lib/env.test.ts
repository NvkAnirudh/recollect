import { describe, expect, it } from "vitest";

import { parsePublicEnv } from "@/lib/env";

const valid = {
  NEXT_PUBLIC_API_URL: "http://localhost:8000",
  NEXT_PUBLIC_SUPABASE_URL: "http://127.0.0.1:54321",
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_x",
};

describe("parsePublicEnv", () => {
  it("accepts a complete config", () => {
    expect(parsePublicEnv(valid)).toEqual(valid);
  });

  it("names every missing or invalid variable", () => {
    expect(() =>
      parsePublicEnv({
        ...valid,
        NEXT_PUBLIC_API_URL: "not a url",
        NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: undefined,
      }),
    ).toThrow(/NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY/);
  });
});
