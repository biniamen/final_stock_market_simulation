import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-layout',
  templateUrl: './layout.component.html',
  styleUrls: ['./layout.component.css']
})
export class LayoutComponent implements OnInit {
  isLoggedIn = false;
  userRole: string | null = null;
  username: string | null = null;
  kycStatus = false;
  companyName: string | null = null;
  account_balance: string | null = null;
  profit_balance: string | null = null;
  companySector: string | null = null;

  ngOnInit(): void {
    // Check if the user is logged in
    this.isLoggedIn = !!localStorage.getItem('access_token');
    
    if (this.isLoggedIn) {
      // Fetch user details from local storage
      this.userRole = localStorage.getItem('role');
      this.username = localStorage.getItem('username');
      this.account_balance = localStorage.getItem('account_balance');
      this.profit_balance = localStorage.getItem('profit_balance');
      this.kycStatus = localStorage.getItem('kyc_status') === 'true';

      // Fetch company details if the user is a company_admin
      if (this.userRole === 'company_admin') {
        this.companyName = localStorage.getItem('company_name');
        this.companySector = localStorage.getItem('company_sector');
      }
    }
  }

  // Handle logout
  onLogout(): void {
    localStorage.clear(); // Clear all stored data
    this.isLoggedIn = false; // Update logged-in status
    window.location.href = '/login'; // Redirect to login page
  }
}
