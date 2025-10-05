import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Area, AreaChart } from "recharts";
import { TrendingUp } from "lucide-react";

const data = [
  { time: "00:00", actual: 1200, predicted: 1180, optimal: 1150 },
  { time: "03:00", actual: 950, predicted: 980, optimal: 920 },
  { time: "06:00", actual: 1100, predicted: 1120, optimal: 1080 },
  { time: "09:00", actual: 1650, predicted: 1680, optimal: 1620, peak: true },
  { time: "12:00", actual: 2100, predicted: 2150, optimal: 2050 },
  { time: "15:00", actual: 1980, predicted: 1950, optimal: 1900 },
  { time: "18:00", actual: 2250, predicted: 2280, optimal: 2200, peak: true },
  { time: "21:00", actual: 1450, predicted: 1480, optimal: 1420 },
  { time: "24:00", actual: null, predicted: 1220, optimal: 1180 },
  { time: "+3hr", actual: null, predicted: 1050, optimal: 1020 },
];

export function PredictiveChart() {
  return (
    <Card className="gradient-card border-border/50 col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary" />
          2-Hour Predictive Analytics (15-min intervals)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--accent))" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="hsl(var(--accent))" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorOptimal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--secondary))" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="hsl(var(--secondary))" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
            <XAxis 
              dataKey="time" 
              stroke="hsl(var(--muted-foreground))"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              style={{ fontSize: '12px' }}
              label={{ value: 'kW', angle: -90, position: 'insideLeft', style: { fill: 'hsl(var(--muted-foreground))' } }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                boxShadow: 'var(--shadow-elevated)'
              }}
            />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="actual" 
              stroke="hsl(var(--primary))" 
              strokeWidth={2}
              fill="url(#colorActual)"
              name="Actual Usage"
            />
            <Area 
              type="monotone" 
              dataKey="predicted" 
              stroke="hsl(var(--accent))" 
              strokeWidth={2}
              strokeDasharray="5 5"
              fill="url(#colorPredicted)"
              name="AI Prediction"
            />
            <Area 
              type="monotone" 
              dataKey="optimal" 
              stroke="hsl(var(--secondary))" 
              strokeWidth={2}
              fill="url(#colorOptimal)"
              name="Optimal Target"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
