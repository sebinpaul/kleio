"use client";

import Link from "next/link";
import { useClerk, useUser } from "@clerk/nextjs";
import { ArrowUpRight, MoreHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function UserMenu() {
  const { user } = useUser();
  const { signOut, openUserProfile } = useClerk();

  const email =
    user?.primaryEmailAddress?.emailAddress ??
    user?.emailAddresses?.[0]?.emailAddress ??
    "Account";
  const initial =
    user?.firstName?.[0]?.toUpperCase() ??
    email[0]?.toUpperCase() ??
    "U";
  const imageUrl = user?.imageUrl;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="h-auto w-full justify-start gap-3 rounded-xl bg-gradient-to-r from-slate-50 to-indigo-50 px-3 py-3 hover:from-slate-100 hover:to-indigo-100"
        >
          {imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imageUrl}
              alt=""
              className="h-10 w-10 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white">
              {initial}
            </div>
          )}
          <span className="min-w-0 flex-1 truncate text-left text-sm font-semibold text-slate-900">
            {email}
          </span>
          <MoreHorizontal className="size-4 text-slate-500" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        side="top"
        align="start"
        sideOffset={8}
        className="w-64 rounded-xl"
      >
        <DropdownMenuGroup>
          <DropdownMenuItem onSelect={() => openUserProfile()}>
            My profile
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/">
              Homepage
              <ArrowUpRight className="ml-auto size-3.5 text-muted-foreground" />
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/dashboard/settings">Settings</Link>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onSelect={() => {
            void signOut({ redirectUrl: "/" });
          }}
        >
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
