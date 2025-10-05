import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Brain } from "lucide-react";
import { Progress } from "@/components/ui/progress";

const trainingData = [
  { episode: 0, reward: -100000, cost: 100000 },
  { episode: 200, reward: -85000, cost: 85000 },
  { episode: 400, reward: -72000, cost: 72000 },
  { episode: 600, reward: -67000, cost: 67000 },
  { episode: 800, reward: -65000, cost: 65000 },
  { episode: 1000, reward: -64065, cost: 64065 },
];

export function TrainingProgress() {
  const currentEpisodes = 1000;
  const targetEpisodes = 10000;
  const progress = (currentEpisodes / targetEpisodes) * 100;

  return (
    <Card className="gradient-card border-border/50 lg:col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary glow-primary" />
          Deep RL Training Progress (PPO Algorithm)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Training Episodes</span>
            <span className="font-medium">{currentEpisodes.toLocaleString()} / {targetEpisodes.toLocaleString()}</span>
          </div>
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-muted-foreground">
            Training on 10-year synthetic dataset (350,688 data points from real Indian solar plant)
          </p>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={trainingData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="episode" 
              stroke="hsl(var(--muted-foreground))"
              label={{ value: 'Training Episodes', position: 'insideBottom', offset: -5 }}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              label={{ value: 'Daily Cost (₹)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="cost" 
              stroke="hsl(var(--primary))" 
              strokeWidth={2}
              dot={{ fill: 'hsl(var(--primary))', r: 4 }}
              name="Daily Cost"
            />
          </LineChart>
        </ResponsiveContainer>

        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border/50">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Model Size</p>
            <p className="text-lg font-bold">50 MB</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Inference Time</p>
            <p className="text-lg font-bold text-secondary">0.43 ms</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Network Params</p>
            <p className="text-lg font-bold">74K</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
