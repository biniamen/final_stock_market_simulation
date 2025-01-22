import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
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

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadDashboard();
    this.username = localStorage.getItem('username');
    this.kycStatus = localStorage.getItem('kyc_status');
  }

  loadDashboard(): void {
    this.isLoading = true;
    this.error = '';

    // Replace with your actual base URL
    this.http.get<any>('http://127.0.0.1:8000/api/stocks/dashboard/').subscribe({
      next: (data) => {
        this.dashboardData = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Dashboard error:', err);
        this.error = 'Failed to load dashboard data.';
        this.isLoading = false;
      }
    });
  }
 

}
