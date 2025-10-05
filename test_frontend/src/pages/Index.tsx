import { DashboardHeader } from "@/components/Dashboard/Header";
import { MetricCard } from "@/components/Dashboard/MetricCard";
import { EnergyFlow } from "@/components/Dashboard/EnergyFlow";
import { PredictiveChart } from "@/components/Dashboard/PredictiveChart";
import { AIInsights } from "@/components/Dashboard/AIInsights";
import { EnergyBreakdown } from "@/components/Dashboard/EnergyBreakdown";
import { ROICalculator } from "@/components/Dashboard/ROICalculator";
import { CarbonImpact } from "@/components/Dashboard/CarbonImpact";
import { SystemArchitecture } from "@/components/Dashboard/SystemArchitecture";
import { PerformanceComparison } from "@/components/Dashboard/PerformanceComparison";
import { TrainingProgress } from "@/components/Dashboard/TrainingProgress";
import { Zap, TrendingDown, DollarSign, Gauge } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />
      
      <main className="container mx-auto px-6 py-8">
        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Current Consumption"
            value="1,800 kW"
            change="Peak hour: 2,250 kW"
            icon={Zap}
            trend="up"
            color="primary"
          />
          <MetricCard
            title="Cost Savings (AI vs Rule-Based)"
            value="36%"
            change="Target: 40-50% (10K episodes)"
            icon={TrendingDown}
            trend="up"
            color="secondary"
          />
          <MetricCard
            title="Annual Savings"
            value="₹1.66Cr"
            change="Payback: 3.25 months"
            icon={DollarSign}
            trend="up"
            color="accent"
          />
          <MetricCard
            title="System Reliability"
            value="100%"
            change="Zero blackouts, 2 violations/day"
            icon={Gauge}
            trend="up"
            color="primary"
          />
        </div>

        {/* Energy Flow */}
        <div className="mb-8">
          <EnergyFlow />
        </div>

        {/* Performance Comparison */}
        <div className="mb-8">
          <PerformanceComparison />
        </div>

        {/* Charts & Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <PredictiveChart />
          <EnergyBreakdown />
        </div>

        {/* Training Progress */}
        <div className="mb-8">
          <TrainingProgress />
        </div>

        {/* System Architecture */}
        <div className="mb-8">
          <SystemArchitecture />
        </div>

        {/* ROI & Carbon Impact */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ROICalculator />
          <CarbonImpact />
        </div>

        {/* AI Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AIInsights />
          
          {/* System Status Card */}
          <div className="gradient-card border-border/50 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-secondary animate-pulse glow-secondary" />
              System Health Monitor
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">PPO Algorithm Status</span>
                <span className="text-sm font-medium text-secondary">Active</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Model Inference Time</span>
                <span className="text-sm font-medium">0.43 ms</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Decisions Today</span>
                <span className="text-sm font-medium">96 (every 15 min)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Training Dataset</span>
                <span className="text-sm font-medium">10-year synthetic</span>
              </div>
              <div className="pt-4 border-t border-border/50">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full gradient-accent rounded-full animate-pulse" style={{ width: "94%" }} />
                  </div>
                  <span className="text-xs font-medium">94%</span>
                </div>
                <p className="text-xs text-muted-foreground mt-2">Overall System Performance</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
