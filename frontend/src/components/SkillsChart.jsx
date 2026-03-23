import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const COLORS = ["#1976d2", "#42a5f5", "#90caf9", "#bbdefb", "#e3f2fd"];

export default function SkillsChart({ skills }) {
  if (!skills || skills.length === 0) return null;
  const data = skills.slice(0, 10).map((s) => ({ name: s, value: 1 }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 12 }} />
        <Tooltip formatter={() => ["Present", "Skill"]} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
