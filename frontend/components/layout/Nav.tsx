"use client";

import { useEffect, useState } from "react";
import { APP_NAME, NAV_LINKS } from "@/lib/constants";

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={`sticky top-0 z-20 flex items-center justify-between py-6 transition-colors ${
        scrolled ? "bg-paper shadow-[0_1px_0_theme(colors.line)]" : ""
      }`}
    >
      <div className="font-display italic font-bold text-xl">{APP_NAME}</div>

      <div className="hidden sm:flex gap-8 text-[15px]">
        {NAV_LINKS.map((link) => (
          <a
            key={link.href}
            href={link.href}
            className="opacity-75 hover:opacity-100 transition-opacity no-underline"
          >
            {link.label}
          </a>
        ))}
      </div>

      <button className="flex-none rounded-sm bg-ink px-[18px] py-[10px] text-sm text-paper">
        Try it free
      </button>
    </nav>
  );
}
