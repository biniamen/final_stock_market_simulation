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
@Component({
  selector: 'app-auth-login',
  templateUrl: './auth-login.component.html',
  styleUrls: ['./auth-login.component.css']
})

export class AuthLoginComponent implements OnInit {
  loginUser = { username: '', password: '' };
  companyDetails: any = null; // Store company details

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

  onLogin() {
    this.authService.login(this.loginUser).subscribe(
      (response) => {
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
        localStorage.setItem('username', response.username);
        localStorage.setItem('kyc_status', response.kyc_verified);
        localStorage.setItem('role', response.role);
        localStorage.setItem('company_id', response.company_id);
        localStorage.setItem('user_id', response.id);
        localStorage.setItem('account_balance', response.account_balance);
        localStorage.setItem('profit_balance', response.profit_balance);

        this.toastr.success('Login successful!', 'Success');

        if (response.role === 'company_admin') {
          this.fetchCompanyDetails(response.company_id); // Fetch company details for company_admin
        }

        this.router.navigate(['/home']);
      },
      (error) => {
        console.error('Login error:', error);
        if (error.error && error.error.detail) {
          this.toastr.error(error.error.detail, 'Error');
        } else {
          this.toastr.error('Login failed. Check your credentials.', 'Error');
        }
      }
    );
  }

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
  
}
