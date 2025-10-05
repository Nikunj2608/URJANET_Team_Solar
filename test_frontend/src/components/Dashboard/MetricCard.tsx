import { LucideIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MetricCardProps {
  title: string;
  value: string;
  change: string;
  icon: LucideIcon;
  trend: "up" | "down";
  color?: "primary" | "secondary" | "accent";
}

export function MetricCard({ title, value, change, icon: Icon, trend, color = "primary" }: MetricCardProps) {
  const colorClasses = {
    primary: "text-primary bg-primary/10 border-primary/20",
    secondary: "text-secondary bg-secondary/10 border-secondary/20",
    accent: "text-accent bg-accent/10 border-accent/20",
  };

  const glowClasses = {
    primary: "glow-primary",
    secondary: "glow-secondary",
    accent: "",
  };

  return (
    <Card className="gradient-card border-border/50 hover:border-primary/30 transition-all duration-300 hover:shadow-elevated">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center justify-between">
          {title}
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorClasses[color]} ${glowClasses[color]}`}>
            <Icon className="w-5 h-5" />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="text-3xl font-bold">{value}</div>
          <p className={`text-sm flex items-center gap-1 ${trend === "up" ? "text-secondary" : "text-accent"}`}>
            <span>{trend === "up" ? "↑" : "↓"}</span>
            <span>{change}</span>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
