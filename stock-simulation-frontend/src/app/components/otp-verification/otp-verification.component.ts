import { HttpClient } from "@angular/common/http";
import { Component } from "@angular/core";
import { ActivatedRoute, Router } from "@angular/router";
@Component({
  selector: 'app-otp-verification',
  templateUrl: './otp-verification.component.html',
  styleUrls: ['./otp-verification.component.css']
})
export class OtpVerificationComponent {
  email: string = '';
  otpCode: string = '';
  attemptsExceeded: boolean = false;
  successMessage: string = '';
  errorMessage: string = '';
  showResend: boolean = false;

  constructor(
    private http: HttpClient,
    private route: ActivatedRoute,
    private router: Router
  ) {
    this.route.queryParams.subscribe((params) => {
      this.email = params['email'];
    });
  }

  verifyOTP() {
    this.http
      .post('http://127.0.0.1:8000/api/users/verify-otp/', { email: this.email, otp_code: this.otpCode })
      .subscribe(
        (response: any) => {
          this.successMessage = response.detail;
          this.errorMessage = '';
          this.showResend = false;
          setTimeout(() => this.router.navigate(['/kyc-pending']), 2000); // Redirect after success
        },
        (error) => {
          this.errorMessage = error.error.detail;
          if (error.error.resend_required) {
            this.attemptsExceeded = true;
            this.showResend = true;
          }
        }
      );
  }

  resendOTP() {
    this.http.post('http://127.0.0.1:8000/api/users/resend-otp/', { email: this.email }).subscribe(
      (response: any) => {
        this.successMessage = response.detail;
        this.attemptsExceeded = false;
        this.showResend = false;
      },
      (error) => {
        this.errorMessage = error.error.detail;
      }
    );
  }
}
