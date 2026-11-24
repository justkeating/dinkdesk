import { Children, Suspense } from "react";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { logout } from "./login/action";
export default function Home() {
  return (
    <main className="mx-auto w-full max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">Dinkdesk</h1>

      {/* Reading the session uses cookies, which only exist at request time.
          With cacheComponents on, that has to sit inside a Suspense boundary:
          the heading above is prerendered, and this part streams in. */}
      <Suspense fallback={<p className="mt-6 text-zinc-500">Loading…</p>}>
        <CurrentUser >
          <form action={logout} className="mt-6 space-y-4">
            <button 
              type="submit"
              className="rounded bg-zinc-900 px-3 py-1 text-sm text-zinc-100 hover:bg-zinc-700"
            >
              Sign out
            </button>
          </form>
        </CurrentUser>
      </Suspense>
    </main>
  );
}

async function CurrentUser({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();

  // The page checks for itself, not just proxy.ts. If the proxy's matcher
  // ever stops covering this route, this line still protects it.
  const { data } = await supabase.auth.getClaims();
  if (!data?.claims) {
    redirect("/login");
  }
  const userId = data.claims.sub;

  // No filter here on purpose: RLS decides which rows come back.
  const { data: clients } = await supabase
    .from("clients")
    .select("id, name, coach_id, user_id");

  const isCoach = clients?.some((c) => c.coach_id === userId);
  const isClient = clients?.some((c) => c.user_id === userId);
  const role = isCoach ? "coach" : isClient ? "client" : "unknown";

  return (

    <section className="mt-6 space-y-4">
      <p>
        Signed in as <strong>{data.claims.email}</strong> ({role})
      </p>

      <div>
        <h2 className="font-medium">Client rows RLS lets you see</h2>
        <ul className="mt-2 list-disc pl-6">
          {clients?.map((c) => <li key={c.id}>{c.name}</li>)}
        </ul>
      </div>
      {children}
    </section>
  );
}
