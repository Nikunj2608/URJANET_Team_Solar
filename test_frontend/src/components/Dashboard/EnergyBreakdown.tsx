import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { Leaf } from "lucide-react";

const data = [
  { name: "Solar", value: 42, color: "hsl(var(--accent))" },
  { name: "Wind", value: 28, color: "hsl(var(--primary))" },
  { name: "Grid (Green)", value: 18, color: "hsl(var(--secondary))" },
  { name: "Grid (Traditional)", value: 12, color: "hsl(var(--muted))" },
];

export function EnergyBreakdown() {
  return (
    <Card className="gradient-card border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Leaf className="w-5 h-5 text-secondary" />
          Energy Source Distribution
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="mt-4 pt-4 border-t border-border/50">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Renewable Energy</span>
            <span className="font-bold text-secondary">88%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
