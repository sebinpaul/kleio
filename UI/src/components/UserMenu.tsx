"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useClerk, useUser } from "@clerk/nextjs";
import { ArrowUpRight, Monitor, Moon, MoreHorizontal, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type Theme = "light" | "dark" | "system";

const THEME_KEY = "kleio-theme";

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const dark = theme === "dark" || (theme === "system" && prefersDark);
  root.classList.toggle("dark", dark);
}

function readStoredTheme(): Theme {
  if (typeof window === "undefined") return "system";
  const stored = window.localStorage.getItem(THEME_KEY);
  if (stored === "light" || stored === "dark" || stored === "system") return stored;
  return "system";
}

export default function UserMenu() {
  const { user } = useUser();
  const { signOut, openUserProfile } = useClerk();
  const [theme, setTheme] = useState<Theme>("system");

  useEffect(() => {
    const initial = readStoredTheme();
    setTheme(initial);
    applyTheme(initial);
  }, []);

  const setAndStoreTheme = (next: Theme) => {
    setTheme(next);
    window.localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  };

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
          variant="secondary"
          className="h-auto w-full justify-start gap-3 rounded-full px-2.5 py-2"
        >
          {imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imageUrl}
              alt=""
              className="h-9 w-9 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-900 text-sm font-semibold text-white dark:bg-zinc-100 dark:text-zinc-900">
              {initial}
            </div>
          )}
          <span className="min-w-0 flex-1 truncate text-left text-sm font-medium">
            {email}
          </span>
          <MoreHorizontal className="size-4 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        side="top"
        align="start"
        sideOffset={8}
        className="w-64 rounded-2xl border-border bg-zinc-950 p-1.5 text-zinc-100 shadow-2xl dark:bg-zinc-950"
      >
        <DropdownMenuGroup>
          <DropdownMenuItem
            className="rounded-xl px-3 py-2.5 text-zinc-200 focus:bg-white/10 focus:text-zinc-100"
            onSelect={() => openUserProfile()}
          >
            My profile
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <div className="flex items-center justify-between gap-2 rounded-xl bg-white/5 px-3 py-2 text-sm text-zinc-200">
          <span>Appearance</span>
          <DropdownMenuRadioGroup
            value={theme}
            onValueChange={(value) => setAndStoreTheme(value as Theme)}
            className="flex items-center rounded-lg bg-zinc-900 p-0.5"
          >
            <DropdownMenuRadioItem
              value="light"
              className="rounded-md p-1.5 pl-1.5 text-zinc-400 focus:bg-zinc-700 focus:text-white data-[state=checked]:bg-zinc-700 data-[state=checked]:text-white [&>span:first-child]:hidden"
              aria-label="Light"
            >
              <Sun className="size-3.5" />
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem
              value="dark"
              className="rounded-md p-1.5 pl-1.5 text-zinc-400 focus:bg-zinc-700 focus:text-white data-[state=checked]:bg-zinc-700 data-[state=checked]:text-white [&>span:first-child]:hidden"
              aria-label="Dark"
            >
              <Moon className="size-3.5" />
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem
              value="system"
              className="rounded-md p-1.5 pl-1.5 text-zinc-400 focus:bg-zinc-700 focus:text-white data-[state=checked]:bg-zinc-700 data-[state=checked]:text-white [&>span:first-child]:hidden"
              aria-label="System"
            >
              <Monitor className="size-3.5" />
            </DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
        </div>

        <DropdownMenuSeparator className="bg-white/10" />

        <DropdownMenuGroup>
          <DropdownMenuItem
            asChild
            className="rounded-xl px-3 py-2.5 text-zinc-200 focus:bg-white/10 focus:text-zinc-100"
          >
            <Link href="/">
              Homepage
              <ArrowUpRight className="ml-auto size-3.5 text-zinc-500" />
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem
            asChild
            className="rounded-xl px-3 py-2.5 text-zinc-200 focus:bg-white/10 focus:text-zinc-100"
          >
            <Link href="/dashboard">Onboarding</Link>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator className="bg-white/10" />

        <DropdownMenuItem
          className="rounded-xl px-3 py-2.5 text-zinc-200 focus:bg-white/10 focus:text-zinc-100"
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
