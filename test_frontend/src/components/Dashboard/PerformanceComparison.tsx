import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { TrendingDown } from "lucide-react";

const data = [
  {
    metric: 'Daily Cost',
    'Random Policy': 100000,
    'Rule-Based': 63815,
    'AI (Current)': 64065,
    'AI (Target)': 50000,
  },
  {
    metric: 'Emissions',
    'Random Policy': 11891,
    'Rule-Based': 8500,
    'AI (Current)': 7277,
    'AI (Target)': 6500,
  },
  {
    metric: 'Violations/Day',
    'Random Policy': 150,
    'Rule-Based': 68,
    'AI (Current)': 2,
    'AI (Target)': 0,
  },
];

export function PerformanceComparison() {
  return (
    <Card className="gradient-card border-border/50 lg:col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingDown className="w-5 h-5 text-secondary" />
          Performance Comparison: AI vs Traditional Systems
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="metric" stroke="hsl(var(--muted-foreground))" />
            <YAxis stroke="hsl(var(--muted-foreground))" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Bar dataKey="Random Policy" fill="hsl(var(--muted))" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Rule-Based" fill="hsl(var(--accent))" radius={[4, 4, 0, 0]} />
            <Bar dataKey="AI (Current)" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
            <Bar dataKey="AI (Target)" fill="hsl(var(--secondary))" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>

        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border/50">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Cost Savings</p>
            <p className="text-2xl font-bold text-secondary">36%</p>
            <p className="text-xs text-muted-foreground">Target: 40-50%</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Emission Reduction</p>
            <p className="text-2xl font-bold text-secondary">39%</p>
            <p className="text-xs text-muted-foreground">vs. Baseline</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Violation Reduction</p>
            <p className="text-2xl font-bold text-secondary">97%</p>
            <p className="text-xs text-muted-foreground">2 vs 68 daily</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
