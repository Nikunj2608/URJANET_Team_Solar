"""
Synthetic Ambient Data Generator for 10 Years (Indian Context)
Generates realistic monthly weather data with seasonal variations, trends, and Indian climate patterns

This creates training data similar to your XLSX files but with:
- 10 years of historical data (2015-2024)
- Monthly granularity with daily variations
- Indian climate patterns (monsoon, summer, winter)
- Realistic temperature, irradiance, humidity, wind patterns
- Long-term trends (climate change effects)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

class IndianAmbientDataGenerator:
    """Generate synthetic ambient weather data for Indian locations"""
    
    def __init__(self, location="North India", seed=42):
        """
        Initialize generator with Indian climate parameters
        
        Args:
            location: 'North India', 'South India', 'Central India', 'Coastal India'
            seed: Random seed for reproducibility
        """
        self.location = location
        np.random.seed(seed)
        
        # Indian climate patterns by location
        self.climate_params = self._get_climate_params(location)
        
    def _get_climate_params(self, location):
        """Get climate parameters for different Indian regions"""
        
        if location == "North India":
            return {
                'temp_base': 25.0,  # Base temperature (°C)
                'temp_amplitude': 15.0,  # Seasonal variation
                'temp_trend': 0.03,  # Annual warming trend (°C/year)
                'monsoon_months': [6, 7, 8, 9],  # June-September
                'monsoon_intensity': 1.5,
                'summer_months': [4, 5, 6],  # April-June
                'summer_peak': 42.0,  # Peak summer temp
                'winter_months': [12, 1, 2],  # Dec-Feb
                'winter_low': 8.0,  # Lowest winter temp
                'irradiance_max': 1000,  # W/m² (clear sky)
                'humidity_base': 60,  # Base humidity %
                'wind_speed_avg': 3.5,  # m/s
            }
        elif location == "South India":
            return {
                'temp_base': 28.0,
                'temp_amplitude': 8.0,  # Less variation
                'temp_trend': 0.025,
                'monsoon_months': [6, 7, 8, 9, 10, 11],  # Longer monsoon
                'monsoon_intensity': 1.3,
                'summer_months': [3, 4, 5],
                'summer_peak': 38.0,
                'winter_months': [12, 1],
                'winter_low': 18.0,
                'irradiance_max': 950,
                'humidity_base': 75,  # Higher humidity
                'wind_speed_avg': 4.0,
            }
        elif location == "Central India":
            return {
                'temp_base': 27.0,
                'temp_amplitude': 12.0,
                'temp_trend': 0.028,
                'monsoon_months': [6, 7, 8, 9],
                'monsoon_intensity': 1.4,
                'summer_months': [4, 5, 6],
                'summer_peak': 45.0,  # Very hot
                'winter_months': [12, 1, 2],
                'winter_low': 12.0,
                'irradiance_max': 1050,
                'humidity_base': 55,
                'wind_speed_avg': 3.0,
            }
        else:  # Coastal India
            return {
                'temp_base': 29.0,
                'temp_amplitude': 6.0,  # Minimal variation
                'temp_trend': 0.022,
                'monsoon_months': [6, 7, 8, 9],
                'monsoon_intensity': 1.8,  # Heavy rainfall
                'summer_months': [4, 5],
                'summer_peak': 35.0,  # Moderate due to sea breeze
                'winter_months': [12, 1],
                'winter_low': 22.0,
                'irradiance_max': 900,
                'humidity_base': 80,  # Very humid
                'wind_speed_avg': 5.0,  # Strong sea breeze
            }
    
    def generate_temperature(self, start_date, end_date):
        """
        Generate realistic temperature data with seasonal patterns and trends
        """
        dates = pd.date_range(start_date, end_date, freq='15min')
        n_points = len(dates)
        
        params = self.climate_params
        
        # Base seasonal pattern (annual cycle)
        day_of_year = dates.dayofyear
        seasonal = params['temp_base'] + params['temp_amplitude'] * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        
        # Long-term warming trend
        years_since_start = (dates.year - dates.year.min())
        trend = params['temp_trend'] * years_since_start
        
        # Daily cycle (cooler at night, hotter at noon)
        hour = dates.hour + dates.minute / 60
        daily_cycle = 5 * np.sin(2 * np.pi * (hour - 6) / 24)
        
        # Monsoon effect (cooler during monsoon)
        monsoon_effect = np.where(dates.month.isin(params['monsoon_months']), -3, 0)
        
        # Random weather variations (day-to-day changes)
        weather_noise = np.random.normal(0, 2, n_points)
        
        # Combine all effects
        temperature = seasonal + trend + daily_cycle + monsoon_effect + weather_noise
        
        # Apply realistic limits
        temperature = np.clip(temperature, params['winter_low'], params['summer_peak'])
        
        return pd.Series(temperature, index=dates, name='ambient_temperature')
    
    def generate_irradiance(self, start_date, end_date, temperature=None):
        """
        Generate solar irradiance data correlated with time of day and season
        """
        dates = pd.date_range(start_date, end_date, freq='15min')
        n_points = len(dates)
        
        params = self.climate_params
        
        # Base irradiance from solar geometry
        hour = dates.hour + dates.minute / 60
        
        # Solar elevation (higher at noon, zero at night)
        solar_elevation = np.maximum(0, np.sin(2 * np.pi * (hour - 6) / 24))
        
        # Seasonal variation (higher in summer)
        day_of_year = dates.dayofyear
        seasonal_factor = 0.85 + 0.15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        
        # Clear sky irradiance
        clear_sky = params['irradiance_max'] * solar_elevation * seasonal_factor
        
        # Cloud cover effects (more clouds during monsoon)
        cloud_factor = np.ones(n_points)
        
        # Monsoon: heavy clouds
        monsoon_mask = dates.month.isin(params['monsoon_months'])
        cloud_factor[monsoon_mask] = np.random.uniform(0.2, 0.6, monsoon_mask.sum())
        
        # Non-monsoon: occasional clouds
        non_monsoon_mask = ~monsoon_mask
        cloud_factor[non_monsoon_mask] = np.random.uniform(0.7, 1.0, non_monsoon_mask.sum())
        
        # Apply cloud factor
        irradiance = clear_sky * cloud_factor
        
        # Add small random fluctuations
        irradiance += np.random.normal(0, 20, n_points)
        
        # Ensure physical limits
        irradiance = np.clip(irradiance, 0, params['irradiance_max'])
        
        return pd.Series(irradiance, index=dates, name='module_temperature')
    
    def generate_humidity(self, start_date, end_date, temperature=None):
        """
        Generate humidity data correlated with temperature and season
        """
        dates = pd.date_range(start_date, end_date, freq='15min')
        n_points = len(dates)
        
        params = self.climate_params
        
        # Base humidity
        humidity = np.ones(n_points) * params['humidity_base']
        
        # Daily cycle (higher at night, lower during day)
        hour = dates.hour + dates.minute / 60
        daily_cycle = 15 * np.sin(2 * np.pi * (hour - 18) / 24)
        
        # Monsoon effect (much higher humidity)
        monsoon_effect = np.where(dates.month.isin(params['monsoon_months']), 25, 0)
        
        # Summer effect (lower humidity due to heat)
        summer_effect = np.where(dates.month.isin(params['summer_months']), -10, 0)
        
        # Temperature anti-correlation (higher temp → lower relative humidity)
        if temperature is not None:
            temp_effect = -0.5 * (temperature - params['temp_base'])
        else:
            temp_effect = 0
        
        # Random variations
        noise = np.random.normal(0, 5, n_points)
        
        # Combine
        humidity = humidity + daily_cycle + monsoon_effect + summer_effect + temp_effect + noise
        
        # Physical limits
        humidity = np.clip(humidity, 20, 100)
        
        return pd.Series(humidity, index=dates, name='relative_humidity')
    
    def generate_wind_speed(self, start_date, end_date):
        """
        Generate wind speed data with diurnal patterns
        """
        dates = pd.date_range(start_date, end_date, freq='15min')
        n_points = len(dates)
        
        params = self.climate_params
        
        # Base wind speed
        wind_speed = np.ones(n_points) * params['wind_speed_avg']
        
        # Daily pattern (stronger during afternoon)
        hour = dates.hour + dates.minute / 60
        daily_cycle = 1.5 * np.sin(2 * np.pi * (hour - 12) / 24)
        
        # Seasonal variation (stronger in summer/monsoon)
        month = dates.month
        seasonal_factor = np.where((month >= 4) & (month <= 9), 1.3, 0.8)
        
        # Monsoon winds (stronger, more variable)
        monsoon_boost = np.where(dates.month.isin(params['monsoon_months']), 
                                 np.random.uniform(0.5, 2.0, n_points), 0)
        
        # Random gusts and calms
        turbulence = np.random.gamma(2, 0.5, n_points)
        
        # Combine
        wind_speed = (wind_speed + daily_cycle + monsoon_boost) * seasonal_factor * turbulence
        
        # Physical limits
        wind_speed = np.clip(wind_speed, 0, 20)
        
        return pd.Series(wind_speed, index=dates, name='wind_speed')
    
    def generate_comprehensive_dataset(self, start_year=2015, end_year=2024):
        """
        Generate complete 10-year dataset with all weather parameters
        """
        start_date = f'{start_year}-01-01'
        end_date = f'{end_year}-12-31 23:45:00'
        
        print(f"Generating synthetic ambient data for {self.location}")
        print(f"Period: {start_year} to {end_year}")
        print(f"Resolution: 15-minute intervals")
        
        # Generate all parameters
        print("\n1. Generating temperature data...")
        temperature = self.generate_temperature(start_date, end_date)
        
        print("2. Generating solar irradiance data...")
        irradiance = self.generate_irradiance(start_date, end_date, temperature)
        
        print("3. Generating humidity data...")
        humidity = self.generate_humidity(start_date, end_date, temperature)
        
        print("4. Generating wind speed data...")
        wind_speed = self.generate_wind_speed(start_date, end_date)
        
        # Combine into DataFrame
        df = pd.DataFrame({
            'DATE_TIME': temperature.index,
            'AMBIENT_TEMPERATURE': temperature.values,
            'MODULE_TEMPERATURE': irradiance.values,  # Using irradiance as proxy for module temp
            'IRRADIATION': irradiance.values,
            'HUMIDITY': humidity.values,
            'WIND_SPEED': wind_speed.values
        })
        
        # Add derived parameters
        df['DC_POWER'] = self._calculate_pv_power(df)
        df['AC_POWER'] = df['DC_POWER'] * 0.96  # Inverter efficiency
        df['DAILY_YIELD'] = self._calculate_daily_yield(df)
        df['TOTAL_YIELD'] = df['DAILY_YIELD'].cumsum()
        
        print(f"\n✓ Generated {len(df):,} data points")
        print(f"✓ Data size: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        return df
    
    def _calculate_pv_power(self, df):
        """Calculate PV power output from weather conditions"""
        # Simplified PV model
        pv_capacity = 3200  # kW
        
        # Base power from irradiance
        power = (df['IRRADIATION'] / 1000) * pv_capacity
        
        # Temperature derating (loses ~0.4% per °C above 25°C)
        temp_factor = 1 - 0.004 * np.maximum(0, df['AMBIENT_TEMPERATURE'] - 25)
        
        # Apply temperature effect
        power *= temp_factor
        
        # Add small random variations (soiling, aging, etc.)
        power *= np.random.uniform(0.95, 1.0, len(df))
        
        return np.maximum(0, power)
    
    def _calculate_daily_yield(self, df):
        """Calculate daily energy yield"""
        df_copy = df.copy()
        df_copy['date'] = df_copy['DATE_TIME'].dt.date
        daily_energy = df_copy.groupby('date')['DC_POWER'].sum() * 0.25  # 15-min intervals
        
        # Map back to original dataframe
        df_copy['daily_yield'] = df_copy['date'].map(daily_energy)
        return df_copy['daily_yield'].values
    
    def save_monthly_files(self, df, output_dir='data/synthetic_10year'):
        """Save data as monthly XLSX files (like your attached files)"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📁 Saving monthly files to: {output_path}")
        
        # Group by year-month
        df['year_month'] = df['DATE_TIME'].dt.to_period('M')
        
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        saved_files = []
        for period, group_df in df.groupby('year_month'):
            year = period.year
            month = period.month
            month_name = month_names[month - 1]
            
            filename = f"{month_name}_{year}.xlsx"
            filepath = output_path / filename
            
            # Drop helper column
            save_df = group_df.drop(columns=['year_month']).copy()
            
            # Save to Excel
            save_df.to_excel(filepath, index=False, engine='openpyxl')
            saved_files.append(filename)
            
            print(f"  ✓ Saved: {filename} ({len(save_df):,} rows)")
        
        print(f"\n✅ Successfully saved {len(saved_files)} monthly files!")
        return saved_files
    
    def generate_summary_statistics(self, df):
        """Generate comprehensive statistics for the dataset"""
        print("\n" + "="*80)
        print("SYNTHETIC AMBIENT DATA - SUMMARY STATISTICS")
        print("="*80)
        
        print(f"\n📊 Dataset Overview:")
        print(f"  • Location: {self.location}")
        print(f"  • Start Date: {df['DATE_TIME'].min()}")
        print(f"  • End Date: {df['DATE_TIME'].max()}")
        print(f"  • Duration: {(df['DATE_TIME'].max() - df['DATE_TIME'].min()).days / 365.25:.1f} years")
        print(f"  • Total Records: {len(df):,}")
        
        print(f"\n🌡️ Temperature Statistics:")
        print(f"  • Mean: {df['AMBIENT_TEMPERATURE'].mean():.2f}°C")
        print(f"  • Min: {df['AMBIENT_TEMPERATURE'].min():.2f}°C")
        print(f"  • Max: {df['AMBIENT_TEMPERATURE'].max():.2f}°C")
        print(f"  • Std Dev: {df['AMBIENT_TEMPERATURE'].std():.2f}°C")
        
        print(f"\n☀️ Irradiance Statistics:")
        print(f"  • Mean: {df['IRRADIATION'].mean():.2f} W/m²")
        print(f"  • Peak: {df['IRRADIATION'].max():.2f} W/m²")
        print(f"  • Daytime Average: {df[df['IRRADIATION'] > 100]['IRRADIATION'].mean():.2f} W/m²")
        
        print(f"\n💧 Humidity Statistics:")
        print(f"  • Mean: {df['HUMIDITY'].mean():.2f}%")
        print(f"  • Min: {df['HUMIDITY'].min():.2f}%")
        print(f"  • Max: {df['HUMIDITY'].max():.2f}%")
        
        print(f"\n🌬️ Wind Speed Statistics:")
        print(f"  • Mean: {df['WIND_SPEED'].mean():.2f} m/s")
        print(f"  • Max: {df['WIND_SPEED'].max():.2f} m/s")
        
        print(f"\n⚡ PV Generation Statistics:")
        print(f"  • Total Energy (10 years): {df['TOTAL_YIELD'].iloc[-1]:,.2f} kWh")
        print(f"  • Average Daily Yield: {df['DAILY_YIELD'].mean():,.2f} kWh/day")
        print(f"  • Peak Power: {df['DC_POWER'].max():.2f} kW")
        print(f"  • Average Capacity Factor: {(df['DC_POWER'].mean() / 3200 * 100):.2f}%")
        
        # Seasonal analysis
        df_copy = df.copy()
        df_copy['month'] = df_copy['DATE_TIME'].dt.month
        monthly_avg = df_copy.groupby('month').agg({
            'AMBIENT_TEMPERATURE': 'mean',
            'IRRADIATION': 'mean',
            'DC_POWER': 'mean'
        })
        
        print(f"\n📅 Seasonal Patterns:")
        print(f"  • Hottest Month: {monthly_avg['AMBIENT_TEMPERATURE'].idxmax()} "
              f"({monthly_avg['AMBIENT_TEMPERATURE'].max():.1f}°C)")
        print(f"  • Coldest Month: {monthly_avg['AMBIENT_TEMPERATURE'].idxmin()} "
              f"({monthly_avg['AMBIENT_TEMPERATURE'].min():.1f}°C)")
        print(f"  • Best PV Month: {monthly_avg['DC_POWER'].idxmax()} "
              f"({monthly_avg['DC_POWER'].max():.1f} kW avg)")
        print(f"  • Worst PV Month: {monthly_avg['DC_POWER'].idxmin()} "
              f"({monthly_avg['DC_POWER'].min():.1f} kW avg)")
    
    def create_visualization(self, df, output_file='synthetic_data_visualization.png'):
        """Create comprehensive visualization of the synthetic data"""
        # Sample data (show 1 month for clarity)
        sample_df = df[df['DATE_TIME'].dt.year == 2024]
        sample_df = sample_df[sample_df['DATE_TIME'].dt.month == 5]  # May
        
        fig, axes = plt.subplots(5, 1, figsize=(16, 12))
        
        hours = np.arange(len(sample_df)) / 96  # Convert to days
        
        # 1. Temperature
        axes[0].plot(hours, sample_df['AMBIENT_TEMPERATURE'], color='red', linewidth=1)
        axes[0].set_ylabel('Temperature (°C)', fontweight='bold')
        axes[0].set_title(f'Synthetic Ambient Data - {self.location} (May 2024 Sample)', 
                         fontsize=14, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        axes[0].set_ylim([0, 50])
        
        # 2. Irradiance
        axes[1].fill_between(hours, 0, sample_df['IRRADIATION'], alpha=0.3, color='orange')
        axes[1].plot(hours, sample_df['IRRADIATION'], color='orange', linewidth=1)
        axes[1].set_ylabel('Irradiance (W/m²)', fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        axes[1].set_ylim([0, 1100])
        
        # 3. Humidity
        axes[2].plot(hours, sample_df['HUMIDITY'], color='blue', linewidth=1)
        axes[2].set_ylabel('Humidity (%)', fontweight='bold')
        axes[2].grid(True, alpha=0.3)
        axes[2].set_ylim([0, 100])
        
        # 4. Wind Speed
        axes[3].plot(hours, sample_df['WIND_SPEED'], color='green', linewidth=1)
        axes[3].set_ylabel('Wind Speed (m/s)', fontweight='bold')
        axes[3].grid(True, alpha=0.3)
        axes[3].set_ylim([0, 20])
        
        # 5. PV Power
        axes[4].fill_between(hours, 0, sample_df['DC_POWER'], alpha=0.3, color='purple')
        axes[4].plot(hours, sample_df['DC_POWER'], color='purple', linewidth=1)
        axes[4].set_ylabel('PV Power (kW)', fontweight='bold')
        axes[4].set_xlabel('Days', fontweight='bold')
        axes[4].grid(True, alpha=0.3)
        axes[4].set_ylim([0, 3500])
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n📊 Visualization saved to: {output_file}")
        plt.close()

def main():
    """Main function to generate 10 years of synthetic data"""
    
    print("="*80)
    print("SYNTHETIC AMBIENT DATA GENERATOR - 10 YEARS (INDIAN CONTEXT)")
    print("="*80)
    print("\nThis will generate 10 years (2015-2024) of realistic weather data")
    print("with Indian climate patterns, seasonal variations, and trends.")
    print("\nSelect location type:")
    print("  1. North India (High temp variation, cold winters)")
    print("  2. South India (Moderate, higher humidity)")
    print("  3. Central India (Very hot summers)")
    print("  4. Coastal India (Minimal variation, very humid)")
    
    # For automated execution, use North India
    location = "North India"
    print(f"\n→ Using: {location}")
    
    # Initialize generator
    generator = IndianAmbientDataGenerator(location=location, seed=42)
    
    # Generate 10 years of data
    print("\n" + "-"*80)
    df = generator.generate_comprehensive_dataset(start_year=2015, end_year=2024)
    
    # Generate statistics
    generator.generate_summary_statistics(df)
    
    # Create visualization
    print("\n" + "-"*80)
    generator.create_visualization(df)
    
    # Save monthly files
    print("\n" + "-"*80)
    saved_files = generator.save_monthly_files(df)
    
    # Save complete dataset
    print("\n" + "-"*80)
    print("💾 Saving complete dataset...")
    complete_file = 'data/synthetic_10year/COMPLETE_10YEAR_DATA.csv'
    df.to_csv(complete_file, index=False)
    print(f"  ✓ Saved: {complete_file} ({len(df):,} rows)")
    
    print("\n" + "="*80)
    print("✅ GENERATION COMPLETE!")
    print("="*80)
    print(f"\n📁 All files saved in: data/synthetic_10year/")
    print(f"  • {len(saved_files)} monthly XLSX files (2015-2024)")
    print(f"  • 1 complete CSV file")
    print(f"  • 1 visualization PNG")
    print(f"\n🎯 You can now train your RL model on 10 years of realistic data!")
    print(f"   Total training samples: {len(df):,} (15-minute resolution)")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
