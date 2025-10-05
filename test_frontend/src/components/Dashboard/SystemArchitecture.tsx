import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Cpu, Shield, Zap } from "lucide-react";

export function SystemArchitecture() {
  return (
    <Card className="gradient-card border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-primary glow-primary" />
          3-Layer System Architecture
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Layer 3: Safety Supervisor */}
        <div className="p-4 rounded-lg bg-accent/10 border border-accent/30">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
              <Shield className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h4 className="font-semibold">Layer 3: Safety Supervisor</h4>
              <p className="text-xs text-muted-foreground">Hard Constraint Enforcement</p>
            </div>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Power Balance</span>
              <span className="text-accent font-medium">±1 kW tolerance</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Battery SoC</span>
              <span className="text-accent font-medium">20-90%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Violations Today</span>
              <span className="text-accent font-medium">2 (vs 68 baseline)</span>
            </div>
          </div>
        </div>

        {/* Layer 2: AI Control Brain */}
        <div className="p-4 rounded-lg bg-primary/10 border border-primary/30">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center glow-primary">
              <Cpu className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h4 className="font-semibold">Layer 2: AI Control Brain</h4>
              <p className="text-xs text-muted-foreground">Deep RL Decision Making (PPO)</p>
            </div>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Observation Space</span>
              <span className="text-primary font-medium">90 dimensions</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Action Space</span>
              <span className="text-primary font-medium">5 continuous</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Inference Time</span>
              <span className="text-primary font-medium">0.43 ms</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Training Episodes</span>
              <span className="text-primary font-medium">1,000 / 10,000</span>
            </div>
          </div>
        </div>

        {/* Layer 1: Physical Assets */}
        <div className="p-4 rounded-lg bg-secondary/10 border border-secondary/30">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-secondary/20 flex items-center justify-center">
              <Zap className="w-5 h-5 text-secondary" />
            </div>
            <div>
              <h4 className="font-semibold">Layer 1: Physical Assets</h4>
              <p className="text-xs text-muted-foreground">Hardware Equipment & Sensors</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Solar PV</span>
              <span className="text-secondary font-medium">3 MW</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Wind</span>
              <span className="text-secondary font-medium">1 MW</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Battery 1</span>
              <span className="text-secondary font-medium">3 MWh</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Battery 2</span>
              <span className="text-secondary font-medium">1 MWh</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Grid</span>
              <span className="text-secondary font-medium">±2 MW</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">EV Charging</span>
              <span className="text-secondary font-medium">122 kW</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
