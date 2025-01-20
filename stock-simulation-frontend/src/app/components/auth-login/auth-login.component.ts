// auth-login.component.ts

import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth.service';
import { HttpClient } from '@angular/common/http';

interface Company {
  id: number;
  company_name: string;
  sector: string;
}

interface Stock {
  id: number;
  company: number;
  ticker_symbol: string;
  total_shares: number;
  current_price: string;
  available_shares: number;
  max_trader_buy_limit: number;
  created_at: string;
  company_name: string;
}

@Component({
  selector: 'app-auth-login',
  templateUrl: './auth-login.component.html',
  styleUrls: ['./auth-login.component.css']
})
export class AuthLoginComponent implements OnInit {
  loginUser = { username: '', password: '' };
  companyDetails: any = null; // Store company details

  // Property to store the reCAPTCHA token
  captchaToken: string | null = null;

  // Property to track form submission
  formSubmitted: boolean = false;

  constructor(
    private authService: AuthService,
    private toastr: ToastrService,
    private router: Router,
    private http: HttpClient // Add HttpClient for API calls
  ) {}

  ngOnInit(): void {
    // Redirect if already logged in
    if (localStorage.getItem('access_token')) {
      this.router.navigate(['/home']);
    }
  }

  // Capture the token from reCAPTCHA
  onCaptchaResolved(token: string | null) {
    this.captchaToken = token;
    console.log('reCAPTCHA token is:', token);
  }

  // Handle user login form submission
  onLogin() {
    this.formSubmitted = true;

    const payload = {
      username: this.loginUser.username,
      password: this.loginUser.password,
      'g-recaptcha-response': this.captchaToken ?? ''
    };

    this.authService.login(payload).subscribe({
      next: (response) => {
        // Since authService already saved the tokens to localStorage,
        // we only need to store extra fields like username, role, etc.
        localStorage.setItem('username', response.username);
        localStorage.setItem('kyc_status', response.kyc_verified);
        localStorage.setItem('role', response.role);
        localStorage.setItem('company_id', String(response.company_id));
        localStorage.setItem('user_id', String(response.id));
        localStorage.setItem('account_balance', String(response.account_balance));
        localStorage.setItem('profit_balance', String(response.profit_balance));

        this.toastr.success('Login successful!', 'Success');

        // If company_admin, fetch company details, then fetch stock
        if (response.role === 'company_admin') {
          const companyId = response.company_id;
          this.fetchCompanyDetails(companyId);
          this.fetchStocksForCompany(companyId);
        }

        // Redirect to home
        this.router.navigate(['/home']);
        this.resetForm();
      },
      error: (error) => {
        console.error('Login error:', error);
        if (error.error && error.error.detail) {
          this.toastr.error(error.error.detail, 'Error');
        } else {
          this.toastr.error('Login failed. Check your credentials.', 'Error');
        }
      },
    });
  }

  // Fetch company details for company_admin
  fetchCompanyDetails(companyId: number) {
    this.http.get<Company>(`http://localhost:8000/api/stocks/companies/${companyId}/`).subscribe(
      (company) => {
        this.companyDetails = company;
        // Store company details in localStorage if needed
        localStorage.setItem('company_name', company.company_name);
        localStorage.setItem('company_sector', company.sector);
      },
      (error) => {
        console.error('Error fetching company details:', error);
      }
    );
  }

  // Fetch all stocks, filter by company_id, then store the first matching stock's ID
  fetchStocksForCompany(companyId: number) {
    this.http.get<Stock[]>(`http://localhost:8000/api/stocks/stocks/`).subscribe(
      (stocks) => {
        const matchingStocks = stocks.filter(stock => stock.company === companyId);

        // If there's at least one stock for this company, store its ID
        if (matchingStocks.length > 0) {
          localStorage.setItem('stock_id', String(matchingStocks[0].id));
          localStorage.setItem('current_price', String(matchingStocks[0].current_price));
          console.log(`Stock ID ${matchingStocks[0].id} stored for company ${companyId}`);
        } else {
          console.warn(`No stocks found for company ${companyId}`);
        }
      },
      (error) => {
        console.error('Error fetching stocks:', error);
      }
    );
  }

  // Reset form after successful login
  resetForm() {
    this.loginUser = { username: '', password: '' };
    this.captchaToken = null;
    this.formSubmitted = false;
    const fileInput = document.getElementById('kycFile') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  }
}
