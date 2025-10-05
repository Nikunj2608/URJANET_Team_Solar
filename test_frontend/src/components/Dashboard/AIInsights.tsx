import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain, ChevronRight, AlertTriangle, CheckCircle, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const insights = [
  {
    type: "success",
    icon: CheckCircle,
    title: "Optimal Performance",
    description: "System operating at 94% efficiency",
    color: "text-secondary",
  },
  {
    type: "warning",
    icon: AlertTriangle,
    title: "Peak Load Predicted",
    description: "High demand expected at 18:00 - Consider load shifting",
    color: "text-accent",
  },
  {
    type: "info",
    icon: Info,
    title: "Renewable Energy Surplus",
    description: "Excess solar available - Recommend battery charging",
    color: "text-primary",
  },
];

export function AIInsights() {
  return (
    <Card className="gradient-card border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary glow-primary" />
          AI Insights & Recommendations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {insights.map((insight, index) => (
            <div
              key={index}
              className="p-4 rounded-lg bg-muted/30 border border-border/50 hover:border-primary/30 transition-all cursor-pointer group"
            >
              <div className="flex items-start gap-3">
                <div className={`mt-0.5 ${insight.color}`}>
                  <insight.icon className="w-5 h-5" />
                </div>
                <div className="flex-1 space-y-1">
                  <p className="font-medium text-sm">{insight.title}</p>
                  <p className="text-xs text-muted-foreground">{insight.description}</p>
                </div>
                <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
