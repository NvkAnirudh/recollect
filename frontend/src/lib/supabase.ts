import { createClient, type SupabaseClient } from "@supabase/supabase-js";

import { getPublicEnv } from "@/lib/env";

let client: SupabaseClient | undefined;

/** Browser Supabase client (auth only; data goes through the Recollect API). */
export function getSupabase(): SupabaseClient {
  if (!client) {
    const env = getPublicEnv();
    client = createClient(env.NEXT_PUBLIC_SUPABASE_URL, env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);
  }
  return client;
}

export async function getAccessToken(): Promise<string | null> {
  const { data } = await getSupabase().auth.getSession();
  return data.session?.access_token ?? null;
}
