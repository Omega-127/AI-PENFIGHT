"use client";

import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Dot } from "recharts";
import type { PerformancePoint } from "@/lib/types";

const SAMPLE_DATA: PerformancePoint[] = [
  { round: 1, score: 32 },
  { round: 2, score: 41 },
  { round: 3, score: 46 },
  { round: 4, score: 68 },
  { round: 5, score: 76 },
  { round: 6, score: 93 },
];

function EndDot(props: any) {
  const { cx, cy, index } = props;
  if (index !== SAMPLE_DATA.length - 1) {
    return <circle cx={cx} cy={cy} r={3.5} fill="#F1E9D8" />;
  }
  return <circle cx={cx} cy={cy} r={6} fill="#7C2436" stroke="#F1E9D8" strokeWidth={2} />;
}

export default function ProgressChart() {
  return (
    <div className="h-[220px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={SAMPLE_DATA} margin={{ top: 20, right: 10, left: 0, bottom: 0 }}>
          <XAxis dataKey="round" hide />
          <YAxis hide domain={[0, 100]} />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#B9862F"
            strokeWidth={2.5}
            dot={<EndDot />}
            isAnimationActive
            animationDuration={1400}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
