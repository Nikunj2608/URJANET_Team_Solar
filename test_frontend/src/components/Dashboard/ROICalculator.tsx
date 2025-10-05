import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TrendingUp, IndianRupee } from "lucide-react";
import { useState } from "react";

export function ROICalculator() {
  const [facilitySize, setFacilitySize] = useState(3); // MW
  
  // Calculations based on spec
  const annualSavings = 1.66; // crore rupees
  const initialInvestment = 4.5 / 100; // crore rupees (4.5 lakh)
  const paybackMonths = 3.25;
  const roi = 3689; // % over 10 years
  const npv = 10.5; // crore rupees over 10 years
  
  const scaledSavings = (annualSavings * facilitySize / 3).toFixed(2);
  const scaledInvestment = (initialInvestment * facilitySize / 3).toFixed(2);

  return (
    <Card className="gradient-card border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-secondary" />
          ROI Calculator
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="facility-size">Facility Peak Demand (MW)</Label>
          <Input
            id="facility-size"
            type="number"
            min="1"
            max="20"
            value={facilitySize}
            onChange={(e) => setFacilitySize(Number(e.target.value))}
            className="bg-muted/30"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Annual Savings</p>
            <p className="text-2xl font-bold text-secondary flex items-center gap-1">
              <IndianRupee className="w-5 h-5" />
              {scaledSavings}Cr
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Initial Investment</p>
            <p className="text-2xl font-bold flex items-center gap-1">
              <IndianRupee className="w-5 h-5" />
              {scaledInvestment}Cr
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Payback Period</p>
            <p className="text-2xl font-bold text-accent">{paybackMonths} mo</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">10-Year ROI</p>
            <p className="text-2xl font-bold text-primary">{roi}%</p>
          </div>
        </div>

        <div className="pt-4 border-t border-border/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">10-Year NPV</span>
            <span className="text-lg font-bold text-secondary flex items-center gap-1">
              <IndianRupee className="w-4 h-4" />
              {(npv * facilitySize / 3).toFixed(1)}Cr
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Break-even Month</span>
            <span className="text-lg font-bold">Month 4</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
