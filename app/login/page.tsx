"use client";
import { useActionState } from "react";
import { login } from "./action";

export default function LoginPage() {
  const [state, formAction, isPending] = useActionState(login, null);

  return (
    <main className="mx-auto w-full max-w-sm p-8">
      <h1 className="text-2xl font-semibold">Sign in</h1>
      <form action={formAction} className="mt-6 flex flex-col gap-3">
        <input type="email" name="email" placeholder="Email" required className="rounded border p-2" />
        <input type="password" name="password" placeholder="Password" required className="rounded border p-2" />
        <button type="submit" disabled={isPending} className="rounded bg-black p-2 text-white disabled:opacity-50">
          {isPending ? "Signing in…" : "Sign in"}
        </button>
        {state?.error && <p className="text-red-600">{state.error}</p>}
      </form>
    </main>
  );
}
