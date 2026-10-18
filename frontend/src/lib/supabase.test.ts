import { beforeEach, describe, expect, it, vi } from "vitest";

const getSession = vi.fn();
const createClient = vi.fn(() => ({ auth: { getSession } }));
vi.mock("@supabase/supabase-js", () => ({ createClient }));

describe("supabase helpers", () => {
  beforeEach(() => {
    vi.resetModules();
    createClient.mockClear();
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "http://127.0.0.1:54321");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_x");
  });

  it("creates the client once from validated env", async () => {
    const { getSupabase } = await import("@/lib/supabase");

    expect(getSupabase()).toBe(getSupabase());
    expect(createClient).toHaveBeenCalledExactlyOnceWith(
      "http://127.0.0.1:54321",
      "sb_publishable_x",
    );
  });

  it("returns the session access token, or null when signed out", async () => {
    const { getAccessToken } = await import("@/lib/supabase");

    getSession.mockResolvedValueOnce({ data: { session: { access_token: "tok" } } });
    await expect(getAccessToken()).resolves.toBe("tok");

    getSession.mockResolvedValueOnce({ data: { session: null } });
    await expect(getAccessToken()).resolves.toBeNull();
  });
});
