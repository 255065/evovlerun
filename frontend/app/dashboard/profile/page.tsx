import { redirect } from "next/navigation";

// The profile editor was consolidated into /dashboard/account. We keep this
// route as a thin redirect so any stale link (header, bookmarks) still
// lands the user on the right page instead of a 404.
export default function ProfileRedirect() {
  redirect("/dashboard/account");
}
