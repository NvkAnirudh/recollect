import { describe, expect, it, vi } from "vitest";

import { ApiError, createApiClient } from "@/lib/api-client";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function setup(response: Response, token: string | null = "tok") {
  const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(response);
  const api = createApiClient({
    baseUrl: "http://api.test",
    getToken: () => Promise.resolve(token),
    fetchImpl,
    timeZone: "Asia/Kolkata",
  });
  const call = () => {
    const [url, init] = fetchImpl.mock.calls[0]!;
    return { url: String(url), init: init!, headers: new Headers(init!.headers) };
  };
  return { api, call };
}

describe("createApiClient", () => {
  it("sends bearer token and timezone, and returns parsed JSON", async () => {
    const { api, call } = setup(jsonResponse(200, { id: "u1" }));

    await expect(api.get("/api/v1/me")).resolves.toEqual({ id: "u1" });
    expect(call().url).toBe("http://api.test/api/v1/me");
    expect(call().headers.get("authorization")).toBe("Bearer tok");
    expect(call().headers.get("x-timezone")).toBe("Asia/Kolkata");
  });

  it("omits Authorization when signed out", async () => {
    const { api, call } = setup(jsonResponse(200, {}), null);

    await api.get("/health");

    expect(call().headers.has("authorization")).toBe(false);
  });

  it("serialises POST bodies as JSON", async () => {
    const { api, call } = setup(jsonResponse(202, { id: "r1" }));

    await api.post("/api/v1/reels", { url: "https://instagram.com/reel/abc" });

    expect(call().init.method).toBe("POST");
    expect(call().headers.get("content-type")).toBe("application/json");
    expect(call().init.body).toBe('{"url":"https://instagram.com/reel/abc"}');
  });

  it("returns undefined for 204", async () => {
    const { api } = setup(new Response(null, { status: 204 }));

    await expect(api.delete("/api/v1/reels/1")).resolves.toBeUndefined();
  });

  it("maps the API error shape to ApiError", async () => {
    const { api } = setup(
      jsonResponse(401, { error: { code: "unauthorized", message: "Token expired" } }),
    );

    const error = await api.get("/api/v1/me").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 401, code: "unauthorized", message: "Token expired" });
  });

  it("falls back to a generic ApiError for non-JSON failures", async () => {
    const { api } = setup(new Response("<html>bad gateway</html>", { status: 502 }));

    await expect(api.get("/x")).rejects.toMatchObject({ status: 502, code: "http_error" });
  });
});
