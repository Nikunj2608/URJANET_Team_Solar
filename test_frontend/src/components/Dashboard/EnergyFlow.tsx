import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Zap, Sun, Wind, Battery } from "lucide-react";

const energySources = [
  { name: "Solar PV", current: 1850, capacity: 3000, color: "text-accent", bgColor: "bg-accent/10", unit: "kW", icon: Sun },
  { name: "Wind Turbine", current: 450, capacity: 1000, color: "text-primary", bgColor: "bg-primary/10", unit: "kW", icon: Wind },
  { name: "Battery 1 (3MWh)", current: 280, capacity: 600, color: "text-secondary", bgColor: "bg-secondary/10", unit: "kW", soc: 65, icon: Battery },
  { name: "Battery 2 (1MWh)", current: 95, capacity: 200, color: "text-secondary", bgColor: "bg-secondary/10", unit: "kW", soc: 72, icon: Battery },
];

export function EnergyFlow() {
  return (
    <Card className="gradient-card border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary" />
          Real-Time Energy Flow
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {energySources.map((source, index) => {
          const percentage = (source.current / source.capacity) * 100;
          const Icon = source.icon;
          
          return (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${source.color}`} />
                  <span className="text-sm font-medium">{source.name}</span>
                </div>
                <span className="text-sm font-medium">
                  {source.current} / {source.capacity} {source.unit}
                  {source.soc && <span className="text-xs text-muted-foreground ml-1">({source.soc}% SoC)</span>}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${source.color.replace('text-', 'bg-')} transition-all duration-500`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground min-w-[45px] text-right">
                  {percentage.toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}

        <div className="pt-4 border-t border-border/50 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Total Renewable Generation</span>
            <span className="font-bold text-secondary">2,300 kW</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Current Building Load</span>
            <span className="font-bold">1,800 kW</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Grid Power</span>
            <span className="font-bold text-accent">-120 kW (Exporting)</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Renewable Utilization</span>
            <span className="font-bold text-secondary">88%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
