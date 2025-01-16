import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { ToastrService } from 'ngx-toastr';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

@Component({
  selector: 'app-auth-register',
  templateUrl: './auth-register.component.html',
  styleUrls: ['./auth-register.component.css']
})
export class AuthRegisterComponent implements OnInit {
  user = { username: '', email: '', password: '', role: 'trader', company_id: null };
  selectedFile: File | null = null;
  companies: any[] = []; // List of available companies

  // 1) Add a property to store the reCAPTCHA token
  captchaToken: string | null = null;

  constructor(
    private authService: AuthService,
    private toastr: ToastrService,
    private router: Router,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    this.loadCompanies();
  }

  loadCompanies() {
    this.http.get<any[]>('http://localhost:8000/api/stocks/companies/').subscribe(
      (data) => {
        this.companies = data;
      },
      (error) => {
        console.error('Error loading companies', error);
        this.toastr.error('Failed to load companies', 'Error');
      }
    );
  }

  // Handle file selection for KYC document
  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  // 2) Capture the token from reCAPTCHA
  onCaptchaResolved(token: string | null) {
    this.captchaToken = token;
    console.log('reCAPTCHA token is:', token);
  }

  // Handle user registration form submission
  onRegister() {
    if (!this.validateEmail(this.user.email)) {
      this.toastr.error('Invalid email format', 'Error');
      return;
    }

    if (this.user.role === 'company_admin' && !this.user.company_id) {
      this.toastr.error('Please select a company for Company Admin role', 'Error');
      return;
    }

    if (!this.selectedFile) {
      this.toastr.error('KYC document is required', 'Error');
      return;
    }

    const formData = new FormData();
    formData.append('username', this.user.username);
    formData.append('email', this.user.email);
    formData.append('password', this.user.password);
    formData.append('role', this.user.role);
    if (this.user.company_id) {
      formData.append('company_id', this.user.company_id);
    }
    formData.append('kyc_document', this.selectedFile);
    
    // 3) Include the reCAPTCHA token in your FormData
    //    (Adjust the field name to match what your backend expects)
     formData.append('g-recaptcha-response', this.captchaToken ?? '');

    // Now call the register service
    this.authService.register(formData).subscribe(
      (response) => {
        console.log('User registered successfully', response);
        this.toastr.success('Registration successful! Waiting For Approval!', 'Success');
        // Redirect to OTP verification page
        this.router.navigate(['/otp-verification'], { queryParams: { email: this.user.email } });
      },
      (error) => {
        console.error('Error registering user', error);
        this.toastr.error('Registration failed. Please try again.', error.detail);
      }
    );
  }

  // Validate email format
  validateEmail(email: string): boolean {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
    return re.test(email);
  }

  // Reset form after successful registration
  resetForm() {
    this.user = { username: '', email: '', password: '', role: 'trader', company_id: null };
    this.selectedFile = null;
    const fileInput = document.getElementById('kycFile') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  }
}
