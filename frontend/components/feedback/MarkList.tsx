import type { Finding } from "@/lib/types";

const DOT_COLOR: Record<Finding["type"], string> = {
  flag: "bg-burgundy",
  tip: "bg-brass",
  good: "bg-[#3E6B4F]",
};

export default function MarkList({ findings }: { findings: Finding[] }) {
  if (findings.length === 0) return null;

  return (
    <div className="mt-4 flex flex-col gap-2">
      {findings.map((f, i) => (
        <div
          key={i}
          className="flex items-start gap-[10px] text-[13.5px] opacity-0 animate-[rise_0.35s_ease_forwards]"
          style={{ animationDelay: `${i * 0.12}s` }}
        >
          <span
            className={`mt-[5px] h-[7px] w-[7px] flex-none rounded-full ${DOT_COLOR[f.type]}`}
          />
          <span>{f.text}</span>
        </div>
      ))}
    </div>
  );
}
