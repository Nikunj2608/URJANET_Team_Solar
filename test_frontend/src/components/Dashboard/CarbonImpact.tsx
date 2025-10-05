import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Leaf, TreeDeciduous } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

const data = [
  { name: 'Traditional', emissions: 11891, color: 'hsl(var(--muted))' },
  { name: 'AI-Optimized', emissions: 7277, color: 'hsl(var(--secondary))' },
];

export function CarbonImpact() {
  const dailyReduction = 4614; // kg CO2
  const annualReduction = 1724; // tonnes CO2
  const treeEquivalent = 86200;
  const reductionPercent = 39;

  return (
    <Card className="gradient-card border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Leaf className="w-5 h-5 text-secondary" />
          Carbon Impact Tracker
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" />
            <YAxis stroke="hsl(var(--muted-foreground))" label={{ value: 'kg CO₂/day', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
            />
            <Bar dataKey="emissions" fill="hsl(var(--secondary))" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Daily Reduction</p>
            <p className="text-2xl font-bold text-secondary">{dailyReduction.toLocaleString()} kg</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Annual Impact</p>
            <p className="text-2xl font-bold text-secondary">{annualReduction} tonnes</p>
          </div>
        </div>

        <div className="pt-4 border-t border-border/50 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground flex items-center gap-2">
              <TreeDeciduous className="w-4 h-4 text-secondary" />
              Equivalent Trees Planted
            </span>
            <span className="text-lg font-bold text-secondary">{treeEquivalent.toLocaleString()}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Emission Reduction</span>
            <span className="text-lg font-bold text-accent">{reductionPercent}%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Grid Carbon Intensity</span>
            <span className="text-sm font-medium">0.82 kg CO₂/kWh</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
