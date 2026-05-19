"use client";

import { useFormStatus } from "react-dom";
import { Button } from "@/components/ui/button";
import { denyOAuthAction } from "./actions";

/**
 * Allow + Deny buttons, split into a client component so we can wire up
 * useFormStatus for the loading spinner. The wrapping form (in page.tsx)
 * carries the consent params as hidden inputs and dispatches approveOAuthAction.
 */
export function ApproveButton() {
  const { pending } = useFormStatus();
  return (
    <>
      <Button type="submit" disabled={pending} className="flex-1">
        {pending ? "Connecting…" : "Allow"}
      </Button>
      <Button
        type="submit"
        variant="ghost"
        formAction={denyOAuthAction}
        disabled={pending}
      >
        Cancel
      </Button>
    </>
  );
}
