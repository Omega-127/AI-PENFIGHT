import { APP_NAME } from "@/lib/constants";

export default function Footer() {
  return (
    <footer className="flex flex-wrap justify-between gap-2 border-t border-line py-8 text-[13px] opacity-60">
      <span>{APP_NAME}</span>
      <span>Built for AI Penfight — v1 preview</span>
    </footer>
  );
}
