"use server";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export async function login(
  prevState: { error: string } | null,
  formData: FormData,
) {
  const supabase = await createClient(); // per request, inside the function

  const { error } = await supabase.auth.signInWithPassword({
    email: String(formData.get("email")),
    password: String(formData.get("password")),
  });

  if (error) {
    return { error: error.message }; // goes back to the form
  }
  redirect("/");
}
