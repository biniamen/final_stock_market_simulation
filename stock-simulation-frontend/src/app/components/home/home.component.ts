// src/app/components/home/home.component.ts

import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { Router } from '@angular/router';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  username: string | null = '';
  kycStatus: string | null = '';

  dashboardData: any = {};
  isLoading: boolean = false;
  error: string = '';

  // ---- Bar Chart Configuration (Top Stocks by Current Price) ----
  public barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: 'Top Stocks by Current Price'
      }
    }
  };

  public barChartLabels: string[] = []; // Ticker symbols
  public barChartData: ChartData<'bar'> = {
    labels: this.barChartLabels,
    datasets: [
      {
        data: [],
        label: 'Current Price',
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }
    ]
  };

  // ---- Pie Chart Configuration (Trader Data: Orders vs Trades) ----
  public pieChartOptions: ChartConfiguration<'pie'>['options'] = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: {
        display: true,
        text: 'Your Orders vs Trades'
      }
    }
  };

  public pieChartLabels: string[] = ['Total Orders', 'Total Trades'];
  public pieChartData: ChartData<'pie'> = {
    labels: this.pieChartLabels,
    datasets: [
      {
        data: [0, 0],
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)'
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)'
        ],
        borderWidth: 1
      }
    ]
  };
  public pieChartType: ChartType = 'pie'; // Correctly typed

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadDashboard();
    this.username = localStorage.getItem('username');
    this.kycStatus = localStorage.getItem('kyc_status');
  }

  loadDashboard(): void {
    this.isLoading = true;
    this.error = '';

    // Replace with your actual API endpoint
    this.http.get<any>('http://127.0.0.1:8000/api/stocks/dashboard/').subscribe({
      next: (data) => {
        this.dashboardData = data;
        this.isLoading = false;
        this.generateBarChartData();
        this.generatePieChartData();
      },
      error: (err) => {
        console.error('Dashboard error:', err);
        this.error = 'Failed to load dashboard data.';
        this.isLoading = false;
      }
    });
  }

  private generateBarChartData(): void {
    this.barChartLabels = [];
    this.barChartData.datasets[0].data = [];

    if (this.dashboardData.top_stocks && Array.isArray(this.dashboardData.top_stocks)) {
      this.dashboardData.top_stocks.forEach((stock: any) => {
        this.barChartLabels.push(stock.ticker_symbol);
        this.barChartData.datasets[0].data.push(Number(stock.current_price));
      });
    }

    // Refresh the chart
    this.barChartData = { ...this.barChartData, labels: this.barChartLabels, datasets: this.barChartData.datasets };
  }

  private generatePieChartData(): void {
    if (this.dashboardData?.user_info?.role === 'trader' && this.dashboardData.trader_data) {
      const totalOrders = this.dashboardData.trader_data.total_orders || 0;
      const totalTrades = this.dashboardData.trader_data.total_trades || 0;
      this.pieChartData.datasets[0].data = [totalOrders, totalTrades];
    }
  }
}
